mod audio;
mod noiseblankerwild;
mod noisereduction;
mod spectralnoisereduction;
mod symphonia_flac;
mod waterfall;

use wasm_bindgen::prelude::*;

use futuredsp::firdes;
use js_sys::Float32Array;

#[wasm_bindgen(start)]
pub fn main() {
    #[cfg(feature = "console_error_panic_hook")]
    console_error_panic_hook::set_once();
}

#[wasm_bindgen]
pub fn greet() {
    // Avoid doing any I/O by default; keep a stable API surface.
}

#[wasm_bindgen]
pub fn firdes_kaiser_lowpass(cutoff: f64, transition_bw: f64, max_ripple: f64) -> Float32Array {
    let fir = firdes::kaiser::lowpass::<f32>(cutoff, transition_bw, max_ripple);
    Float32Array::from(fir.as_slice())
}

pub use audio::{Audio, AudioCodec};
pub use waterfall::ZstdStreamDecoder;
