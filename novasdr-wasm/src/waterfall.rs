use std::io::Write;

use js_sys::Uint8Array;
use wasm_bindgen::prelude::*;
use zstd::stream;

#[wasm_bindgen]
pub struct ZstdStreamDecoder {
    decoder: Option<stream::write::Decoder<'static, Vec<u8>>>,
}

#[wasm_bindgen]
impl ZstdStreamDecoder {
    #[wasm_bindgen(constructor)]
    pub fn new() -> ZstdStreamDecoder {
        let decoder = stream::write::Decoder::new(Vec::new()).ok();
        ZstdStreamDecoder { decoder }
    }

    pub fn clear(&mut self) {
        let Some(decoder) = self.decoder.as_mut() else {
            return;
        };
        decoder.get_mut().clear();
    }

    pub fn decode(&mut self, input: &[u8]) -> Vec<Uint8Array> {
        let Some(decoder) = self.decoder.as_mut() else {
            return Vec::new();
        };

        decoder.get_mut().clear();
        if decoder.write_all(input).is_err() {
            return Vec::new();
        }

        let slice = decoder.get_ref().as_slice();
        if slice.is_empty() {
            return Vec::new();
        }
        vec![Uint8Array::from(slice)]
    }
}
