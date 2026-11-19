# Changelog

## 0.1.0 (2026-11-19)


### Features

* **cli:** add --limit to keep only the first N emails ([5d93a78](https://github.com/Elegary/whocommitted/commit/5d93a78717c52fdc3e76fb1b1691935f5d27b1dd))
* **cli:** add --redact to mask emails and names in every output format ([fea0184](https://github.com/Elegary/whocommitted/commit/fea0184733a48fc88886c50d23cecdbf0e89821d))
* **cli:** add extract command with table, json, csv and txt output ([6738b6f](https://github.com/Elegary/whocommitted/commit/6738b6f94924376d167c061603a8e4c80cb22069))
* **cli:** add multi-key sorting, --reverse and --group-by domain|kind ([c7c001d](https://github.com/Elegary/whocommitted/commit/c7c001d60053d979276035497f048401fe51f700))
* **git:** extract identities from all refs via metadata-only bare clone ([e9e8c34](https://github.com/Elegary/whocommitted/commit/e9e8c3454097781fe220c15db3bc1d005089e962))
* **providers:** resolve github urls, owner/repo shorthand and generic git urls ([c959369](https://github.com/Elegary/whocommitted/commit/c959369c487b34aaf34a4f3880f59c6088e9db1b))
* **scripts:** add script to scan every repository of a github user or org ([1c58ca0](https://github.com/Elegary/whocommitted/commit/1c58ca07501ffb65012498ded2a41d757535d1f8))


### Bug Fixes

* **git:** never let a repository spec be read as a git option ([aade20c](https://github.com/Elegary/whocommitted/commit/aade20c2dca24388dc83a64da6ecc5218ed89a1d))
* **output:** stop rich markup from eating [bot] in emails and names ([f90c643](https://github.com/Elegary/whocommitted/commit/f90c64312890208dbb233315df6f7caa64daa2fb))
* **providers:** resolve ./repo and ../repo as local paths, not owner/repo ([7dd71e5](https://github.com/Elegary/whocommitted/commit/7dd71e58e22aab500b1b61d9719a18d9ae21937f))


### Documentation

* add pip install, use cases and multi-project demo ([1b2196e](https://github.com/Elegary/whocommitted/commit/1b2196e8bb4fbd598558b30b6a2af7ca9fca9deb))
* add protect yourself faq ([9d09433](https://github.com/Elegary/whocommitted/commit/9d094333b6d6ff9888fff951ead21926c85a1bfd))
* mention names alongside email addresses ([e4368ec](https://github.com/Elegary/whocommitted/commit/e4368ece86c4053f5dcfa907a5b98acfcd1151fb))
* redact demo output and move use cases after usage ([5444fe9](https://github.com/Elegary/whocommitted/commit/5444fe9e148cbe6e8c3069cb0a41d3f0579529b4))
* rewrite readme with demo gif and usage examples ([84ec7aa](https://github.com/Elegary/whocommitted/commit/84ec7aa90f2aa7e7e98a26b6211cb669b36a652b))
* write readme ([9842924](https://github.com/Elegary/whocommitted/commit/9842924fdf13f5581f0c0144eac37a8227561ab2))
