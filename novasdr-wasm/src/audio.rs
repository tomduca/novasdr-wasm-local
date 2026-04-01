use std::collections::VecDeque;

use js_sys::Float32Array;
use rubato::{
    Resampler, SincFixedIn, SincInterpolationParameters, SincInterpolationType, WindowFunction,
};
use wasm_bindgen::prelude::*;

use crate::symphonia_flac::FlacStreamDecoder;
use crate::noiseblankerwild::NoiseBlankerWild;
use crate::noisereduction::{NoiseReduction, NoiseReductionType};
use crate::spectralnoisereduction::SpectralNoiseReduction;

#[wasm_bindgen]
pub enum AudioCodec {
    Flac,
    Opus,
}

struct AudioProcessor {
    resampler: Option<SincFixedIn<f32>>,
    queue: VecDeque<f32>,
    nr_enabled: bool,
    nb_enabled: bool,
    an_enabled: bool,
    spectral_nr: SpectralNoiseReduction,
    noise_blanker: NoiseBlankerWild,
    autonotch: NoiseReduction,
}

impl AudioProcessor {
    fn new(input_rate: f64, output_rate: u32) -> Self {
        let resampler = build_resampler(input_rate, output_rate);
        Self {
            resampler,
            queue: VecDeque::new(),
            nr_enabled: false,
            nb_enabled: false,
            an_enabled: false,
            spectral_nr: SpectralNoiseReduction::new(output_rate, 1.0 / 512.0, 0.95, 30.0),
            noise_blanker: NoiseBlankerWild::new(0.95, 10, 7),
            autonotch: NoiseReduction::new(
                NoiseReductionType::Notch,
                64,
                32,
                1.024e-4,
                1.28e-1,
            ),
        }
    }

    fn set_nr(&mut self, enabled: bool) {
        self.nr_enabled = enabled;
    }

    fn set_nb(&mut self, enabled: bool) {
        self.nb_enabled = enabled;
    }

    fn set_an(&mut self, enabled: bool) {
        self.an_enabled = enabled;
    }

    fn process_pcm_f32(&mut self, input: &[f32]) -> Vec<f32> {
        if input.is_empty() {
            return Vec::new();
        }

        self.queue.extend(input.iter().copied());

        let Some(resampler) = self.resampler.as_mut() else {
            return Vec::new();
        };

        let mut out = Vec::<f32>::new();
        while self.queue.len() >= 1024 {
            let mut block = Vec::<f32>::with_capacity(1024);
            for _ in 0..1024 {
                let Some(sample) = self.queue.pop_front() else {
                    break;
                };
                block.push(sample);
            }
            if block.len() != 1024 {
                break;
            }

            let resampled = match resampler.process(&[&block], None) {
                Ok(resampled) => resampled,
                Err(_) => return Vec::new(),
            };
            if resampled.is_empty() {
                continue;
            }
            out.extend_from_slice(&resampled[0]);
        }

        if self.nr_enabled {
            self.spectral_nr.process(&mut out);
        }
        if self.nb_enabled {
            self.noise_blanker.process(&mut out);
        }
        if self.an_enabled {
            self.autonotch.process(&mut out);
        }

        out
    }
}

fn build_resampler(input_rate: f64, output_rate: u32) -> Option<SincFixedIn<f32>> {
    if !input_rate.is_finite() || input_rate <= 0.0 {
        return None;
    }
    if output_rate == 0 {
        return None;
    }

    let params = SincInterpolationParameters {
        sinc_len: 256,
        f_cutoff: 0.95,
        interpolation: SincInterpolationType::Linear,
        oversampling_factor: 256,
        window: WindowFunction::BlackmanHarris2,
    };

    SincFixedIn::<f32>::new(output_rate as f64 / input_rate, 2.0, params, 1024, 1).ok()
}

#[wasm_bindgen]
pub struct Audio {
    codec: AudioCodec,
    flac: FlacStreamDecoder,
    processor: AudioProcessor,
    decoded_callback: Option<js_sys::Function>,
}

#[wasm_bindgen]
impl Audio {
    #[wasm_bindgen(constructor)]
    pub fn new(codec: AudioCodec, _codec_rate: u32, input_rate: f64, output_rate: u32) -> Audio {
        Audio {
            codec,
            flac: FlacStreamDecoder::new(),
            processor: AudioProcessor::new(input_rate, output_rate),
            decoded_callback: None,
        }
    }

    pub fn decode(&mut self, input: &[u8]) -> Float32Array {
        if input.is_empty() {
            return Float32Array::new_with_length(0);
        }

        let decoded_i16 = match self.codec {
            AudioCodec::Flac => self.flac.decode_i16(input),
            AudioCodec::Opus => Vec::new(),
        };

        if decoded_i16.is_empty() {
            return Float32Array::new_with_length(0);
        }

        let decoded_f32 = decoded_i16
            .into_iter()
            .map(|sample| f32::from(sample) / 32768.0)
            .collect::<Vec<f32>>();

        if let Some(callback) = self.decoded_callback.as_mut() {
            let _ = callback.call1(
                &JsValue::NULL,
                &Float32Array::from(decoded_f32.as_slice()),
            );
        }

        let processed = self.processor.process_pcm_f32(&decoded_f32);
        Float32Array::from(processed.as_slice())
    }

    pub fn process_pcm_f32(&mut self, input: &[f32]) -> Float32Array {
        let processed = self.processor.process_pcm_f32(input);
        Float32Array::from(processed.as_slice())
    }

    pub fn set_nr(&mut self, nr: bool) {
        self.processor.set_nr(nr);
    }

    pub fn set_nb(&mut self, nb: bool) {
        self.processor.set_nb(nb);
    }

    pub fn set_an(&mut self, an: bool) {
        self.processor.set_an(an);
    }

    pub fn set_decoded_callback(&mut self, f: Option<js_sys::Function>) {
        self.decoded_callback = f;
    }
}
