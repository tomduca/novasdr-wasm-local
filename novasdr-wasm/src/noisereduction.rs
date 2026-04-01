const ANR_DLINE_SIZE: usize = 512;
const ANR_MASK: usize = ANR_DLINE_SIZE - 1;

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum NoiseReductionType {
    Notch,
    NoiseReduction,
}

pub struct NoiseReduction {
    nr_type: NoiseReductionType,
    in_idx: usize,
    d: [f32; ANR_DLINE_SIZE],
    w: Vec<f32>,
    taps: usize,
    delay: usize,
    two_mu: f32,
    gamma: f32,
    lidx: f32,
    lidx_min: f32,
    lidx_max: f32,
    ngamma: f32,
    den_mult: f32,
    lincr: f32,
    ldecr: f32,
}

impl NoiseReduction {
    pub fn new(
        nr_type: NoiseReductionType,
        nr_taps: usize,
        nr_dly: usize,
        nr_gain: f32,
        nr_leakage: f32,
    ) -> Self {
        let taps = nr_taps.clamp(1, ANR_DLINE_SIZE / 2);
        let delay = nr_dly.clamp(1, taps);
        Self {
            nr_type,
            in_idx: 0,
            d: [0.0; ANR_DLINE_SIZE],
            w: vec![0.0; taps],
            taps,
            delay,
            two_mu: nr_gain,
            gamma: nr_leakage,
            lidx: 120.0,
            lidx_min: 120.0,
            lidx_max: 200.0,
            ngamma: 0.001,
            den_mult: 6.25e-10,
            lincr: 1.0,
            ldecr: 3.0,
        }
    }

    pub fn process(&mut self, buf: &mut [f32]) {
        for sample in buf {
            self.d[self.in_idx] = *sample;

            let mut y = 0.0f32;
            let mut sigma = 0.0f32;
            for j in 0..self.taps {
                let idx = (self.in_idx + j + self.delay) & ANR_MASK;
                let tap_sample = self.d[idx];
                y += self.w[j] * tap_sample;
                sigma += tap_sample * tap_sample;
            }

            let inv_sigp = 1.0 / (sigma + 1.0e-10);
            let error = self.d[self.in_idx] - y;

            let out = match self.nr_type {
                NoiseReductionType::Notch => error,
                NoiseReductionType::NoiseReduction => y * 4.0,
            };
            *sample = out;

            let mut nel = error * (1.0 - self.two_mu * sigma * inv_sigp);
            if nel < 0.0 {
                nel = -nel;
            }

            let mut nev = self.d[self.in_idx]
                - (1.0 - self.two_mu * self.ngamma) * y
                - self.two_mu * error * sigma * inv_sigp;
            if nev < 0.0 {
                nev = -nev;
            }

            if nev < nel {
                self.lidx += self.lincr;
                if self.lidx > self.lidx_max {
                    self.lidx = self.lidx_max;
                }
            } else {
                self.lidx -= self.ldecr;
                if self.lidx < self.lidx_min {
                    self.lidx = self.lidx_min;
                }
            }

            let lidx2 = self.lidx * self.lidx;
            self.ngamma = self.gamma * lidx2 * lidx2 * self.den_mult;

            let c0 = 1.0 - self.two_mu * self.ngamma;
            let c1 = self.two_mu * error * inv_sigp;

            for j in 0..self.taps {
                let idx = (self.in_idx + j + self.delay) & ANR_MASK;
                self.w[j] = c0 * self.w[j] + c1 * self.d[idx];
            }

            self.in_idx = (self.in_idx + ANR_MASK) & ANR_MASK;
        }
    }
}

