---
license: cc-by-4.0
size_categories:
- 100K<n<1M
task_categories:
- text-classification
pretty_name: PhreshPhish
configs:
- config_name: default
  data_files:
  - split: train
    path: "data/train-*.parquet"
  - split: test
    path: "data/test-*.parquet"
---

# PhreshPhish
PhreshPhish is a **large-scale**, **real-world** dataset and benchmark for phishing webpage detection containing phishing and benign HTML-URL pairs.

- **Train** 498,255 samples: 276,729 benign and 221,526 phish
- **Test** 168,060 samples: 91,260 benign and 76,876 phish
- **Benchmarks** 975 benchmarks with base rates ranging from `[5e-4, 1e-3, 5e-3, 1e-2, 5e-2]`

## Changelog

- **v1.0.1 (2026-02-07)**: Added ~200k new samples collected between March and December 2025, improved temporal consistency by downsampling some earlier samples
- **v1.0.0 (2025-05-14)**: Initial release

## Getting Started

```python
from datasets import load_dataset

train = load_dataset('phreshphish/phreshphish', split='train')
test = load_dataset('phreshphish/phreshphish', split='test')
```

## License & Terms of Use

The dataset is released under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/) license and should only be used for anti-phishing research. 

## Citing

If you find our work useful, please consider citing. 

Paper: [PhreshPhish: A Real-World, High-Quality, Large-Scale Phishing Website Dataset and Benchmark](https://huggingface.co/papers/2507.10854)

```bibtex
@article{dalton2025phreshphish,
	title        = {PhreshPhish: A Real-World, High-Quality, Large-Scale Phishing Website Dataset and Benchmark},
	author       = {Thomas Dalton and Hemanth Gowda and Girish Rao and Sachin Pargi and Alireza Hadj Khodabakhshi and Joseph Rombs and Stephan Jou and Manish Marwah},
	year         = 2025,
	journal      = {arXiv preprint},
	url          = {https://arxiv.org/abs/2507.10854},
	eprint       = {2507.10854}
}
```