use futuredsp::{fir::NonResamplingFirKernel, UnaryKernel};

pub struct NoiseBlankerWild {
    thresh: f32,
    taps: usize,
    impulse_samples: usize,
    working_buffer: Vec<f32>,
}

impl NoiseBlankerWild {
    pub fn new(thresh: f32, taps: u32, impulse_samples: u32) -> Self {
        Self {
            thresh,
            taps: taps as usize,
            impulse_samples: impulse_samples as usize,
            working_buffer: Vec::new(),
        }
    }

    pub fn process(&mut self, samps: &mut [f32]) {
        if samps.is_empty() {
            return;
        }

        let impulse_length = self.impulse_samples | 1;
        let pl = (impulse_length - 1) / 2;
        let order = self.taps;

        if order == 0 {
            return;
        }

        let min_len = order + pl + 2;
        if samps.len() < min_len {
            return;
        }

        let mut lpcs = vec![0.0f32; order + 1];
        let mut reverse_lpcs = vec![0.0f32; order + 1];
        let mut tempsamp = vec![0.0f32; samps.len()];
        let mut r = vec![0.0f32; order + 1];
        let mut any = vec![0.0f32; order + 1];
        let mut wfw = vec![0.0f32; impulse_length];
        let mut wbw = vec![0.0f32; impulse_length];

        self.working_buffer
            .resize(2 * pl + 2 * order + samps.len(), 0.0);
        for (i, sample) in samps.iter().enumerate() {
            self.working_buffer[2 * pl + 2 * order + i] = *sample;
        }

        for i in 0..impulse_length {
            wbw[i] = (i as f32) / ((impulse_length as f32) - 1.0);
            wfw[impulse_length - i - 1] = wbw[i];
        }

        for i in 0..(order + 1) {
            let mut acc = 0.0f32;
            for j in 0..(samps.len() - i) {
                acc += self.working_buffer[order + pl + j]
                    * self.working_buffer[order + pl + j + i];
            }
            r[i] = acc;
        }

        r[0] *= 1.0 + 1.0e-9;
        lpcs[0] = 1.0;
        for i in 1..(order + 1) {
            lpcs[i] = 0.0;
        }

        let mut alfa = r[0];
        if alfa == 0.0 {
            return;
        }

        for m in 1..(order + 1) {
            let mut s = 0.0f32;
            for u in 1..m {
                s += lpcs[u] * r[m - u];
            }

            let k = -(r[m] + s) / alfa;

            for v in 1..m {
                any[v] = lpcs[v] + k * lpcs[m - v];
            }

            for w in 1..m {
                lpcs[w] = any[w];
            }

            lpcs[m] = k;
            alfa *= 1.0 - k * k;
            if alfa == 0.0 {
                break;
            }
        }

        for o in 0..(order + 1) {
            reverse_lpcs[order - o] = lpcs[o];
        }

        let lpc = NonResamplingFirKernel::<f32, f32, _, _>::new(reverse_lpcs.clone());
        lpc.work(&mut self.working_buffer[order + pl..], &mut tempsamp[..]);

        let lpc_fwd = NonResamplingFirKernel::<f32, f32, _, _>::new(lpcs.clone());
        let mut tempsamp2 = vec![0.0f32; tempsamp.len()];
        lpc_fwd.work(&mut tempsamp[..], &mut tempsamp2[..]);
        tempsamp.copy_from_slice(&tempsamp2);

        let mean = tempsamp.iter().sum::<f32>() / (tempsamp.len() as f32);
        let sigma2 = tempsamp
            .iter()
            .map(|x| {
                let d = x - mean;
                d * d
            })
            .sum::<f32>()
            / (tempsamp.len() as f32);

        let lpc_power = lpcs.iter().map(|x| x * x).sum::<f32>();
        let impulse_threshold = self.thresh * (sigma2 * lpc_power).sqrt();

        const MAX_IMPULSES: usize = 20;
        let mut impulse_positions = [0usize; MAX_IMPULSES];
        let mut impulse_count = 0usize;
        let mut search_pos = order + pl;

        while search_pos < samps.len() && impulse_count < MAX_IMPULSES {
            if tempsamp[search_pos].abs() > impulse_threshold {
                impulse_positions[impulse_count] = search_pos.saturating_sub(order);
                impulse_count += 1;
                search_pos = search_pos.saturating_add(pl);
            }
            search_pos += 1;
        }

        for i in 1..(order + 1) {
            lpcs[i] = -lpcs[i];
        }
        for i in 0..order {
            reverse_lpcs[i] = -reverse_lpcs[i];
        }

        let mut rfw = vec![0.0f32; impulse_length + order];
        let mut rbw = vec![0.0f32; impulse_length + order];

        for j in 0..impulse_count {
            let pos = impulse_positions[j];
            if pos + order + impulse_length + pl + order + 1 >= self.working_buffer.len() {
                continue;
            }

            for k in 0..order {
                rfw[k] = self.working_buffer[pos + k];
                let idx = order + pl + pos + pl + k + 1;
                rbw[impulse_length + k] = self.working_buffer[idx];
            }

            for i in 0..impulse_length {
                rfw[i + order] = reverse_lpcs[0..order]
                    .iter()
                    .zip(&rfw[i..])
                    .map(|(a, b)| a * b)
                    .sum();
                rbw[impulse_length - i - 1] = lpcs[1..(order + 1)]
                    .iter()
                    .zip(&rbw[impulse_length - i..])
                    .map(|(a, b)| a * b)
                    .sum();
            }

            for i in 0..impulse_length {
                rfw[i + order] *= wfw[i];
                rbw[i] *= wbw[i];
            }

            for i in 0..impulse_length {
                self.working_buffer[order + pos + i] = rfw[order + i] + rbw[i];
            }
        }

        for i in 0..samps.len() {
            samps[i] = self.working_buffer[order + pl + i];
        }

        for i in 0..(2 * order + 2 * pl) {
            self.working_buffer[i] = self.working_buffer[samps.len() + i];
        }
    }
}

