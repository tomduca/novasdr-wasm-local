use std::io::{self, Write};

use ringbuf::{HeapProducer, HeapRb};

use symphonia::core::audio::Signal;
use symphonia::core::codecs::{self, Decoder, DecoderOptions};
use symphonia::core::errors::Error;
use symphonia::core::formats::{FormatOptions, FormatReader};
use symphonia::core::io::{MediaSourceStream, ReadOnlySource};
use symphonia::default::codecs::FlacDecoder;
use symphonia::default::formats::FlacReader;

pub struct FlacStreamDecoder {
    buffered_for_init: Vec<u8>,
    producer: HeapProducer<u8>,
    format: Option<FlacReader>,
    decoder: Option<FlacDecoder>,
    track_id: u32,
}

impl FlacStreamDecoder {
    pub fn new() -> Self {
        let (producer, _consumer) = HeapRb::<u8>::new(2).split();
        Self {
            buffered_for_init: Vec::new(),
            producer,
            format: None,
            decoder: None,
            track_id: 0,
        }
    }

    pub fn reset(&mut self) {
        self.buffered_for_init.clear();
        self.format = None;
        self.decoder = None;
        self.track_id = 0;

        let (producer, _consumer) = HeapRb::<u8>::new(2).split();
        self.producer = producer;
    }

    fn write_all(&mut self, bytes: &[u8]) -> io::Result<()> {
        self.producer.write_all(bytes)
    }

    fn init_if_needed(&mut self, initial_bytes: &[u8]) -> bool {
        if self.decoder.is_some() && self.format.is_some() {
            return true;
        }

        self.buffered_for_init.extend_from_slice(initial_bytes);

        let (producer, consumer) = HeapRb::<u8>::new(1024 * 256).split();
        let source = ReadOnlySource::new(consumer);
        let stream = MediaSourceStream::new(Box::new(source), Default::default());
        self.producer = producer;
        let init_bytes = self.buffered_for_init.clone();
        if self.write_all(&init_bytes).is_err() {
            return false;
        }

        let fmt_opts: FormatOptions = Default::default();
        let format = match FlacReader::try_new(stream, &fmt_opts) {
            Ok(format) => format,
            Err(_) => return false,
        };

        let track = match format
            .tracks()
            .iter()
            .find(|t| t.codec_params.codec != codecs::CODEC_TYPE_NULL)
        {
            Some(track) => track.clone(),
            None => return false,
        };

        let dec_opts: DecoderOptions = Default::default();
        let decoder = match FlacDecoder::try_new(&track.codec_params, &dec_opts) {
            Ok(decoder) => decoder,
            Err(_) => return false,
        };

        self.track_id = track.id;
        self.format = Some(format);
        self.decoder = Some(decoder);
        self.buffered_for_init.clear();
        true
    }

    pub fn decode_i16(&mut self, bytes: &[u8]) -> Vec<i16> {
        if bytes.is_empty() {
            return Vec::new();
        }

        if !self.init_if_needed(bytes) {
            return Vec::new();
        }

        if self.write_all(bytes).is_err() {
            self.reset();
            return Vec::new();
        }

        let Some(format) = self.format.as_mut() else {
            return Vec::new();
        };
        let Some(decoder) = self.decoder.as_mut() else {
            return Vec::new();
        };

        let mut out = Vec::<i16>::new();
        loop {
            let packet = match format.next_packet() {
                Ok(packet) => packet,
                Err(Error::IoError(_)) => break,
                Err(Error::ResetRequired) => {
                    self.reset();
                    break;
                }
                Err(_) => break,
            };

            if packet.track_id() != self.track_id {
                continue;
            }

            match decoder.decode(&packet) {
                Ok(decoded) => {
                    let mut decoded_i16 = decoded.make_equivalent::<i16>();
                    decoded.convert(&mut decoded_i16);
                    out.extend_from_slice(decoded_i16.chan(0));
                }
                Err(Error::IoError(_)) => break,
                Err(Error::ResetRequired) => {
                    self.reset();
                    break;
                }
                Err(_) => break,
            }
        }

        out
    }
}
