# samples

This directory contains sample `water` files that help test
functionality. There are three directories:

* `good` contains files that run successfully and usually
  test a particular feature.
* `bad` contains files that are somehow broken, and test water's
  behavior in certain error conditions. In some cases, the current
  error handling is not great and the samples act as TODO reminders
  to improve those cases.
* `purgatory` contains files which don't currently work, but either
  should work, or should be officially decided to not work. For
  example, partial work toward an implementation of `js:tgp` is
  in this directory (`js:tgp` stands for JavaScript: The Good Parts).
