SublimeLinter-contrib-swipl
================================

[![Build Status](https://travis-ci.org/SublimeLinter/SublimeLinter-contrib-swipl.svg?branch=master)](https://travis-ci.org/SublimeLinter/SublimeLinter-contrib-swipl)

This linter plugin for [SublimeLinter](https://github.com/SublimeLinter/SublimeLinter) provides an interface to [swipl](https://www.swi-prolog.org/). It will be used with files that have the [SWI-Prolog](https://packagecontrol.io/packages/Prolog) syntax.

## Installation
SublimeLinter must be installed in order to use this plugin.

Please use [Package Control](https://packagecontrol.io) to install the linter plugin.

Before installing this plugin, you must ensure that [`swipl`](https://www.swi-prolog.org/Download.html) is installed on your system.

In order for `swipl` to be executed by SublimeLinter, you must ensure that its path is available to SublimeLinter. The docs cover [troubleshooting PATH configuration](http://sublimelinter.readthedocs.io/en/latest/troubleshooting.html#finding-a-linter-executable).

## Settings
- SublimeLinter settings: http://sublimelinter.readthedocs.org/en/latest/settings.html
- Linter settings: http://sublimelinter.readthedocs.org/en/latest/linter_settings.html

Additional SublimeLinter-swipl settings:

* `errors` - Additional error types for check.
	
	Available types: `undefined`, `trivial_fails`, `format_errors`, `redefined`, `void_declarations`, `strings`, `rationals`, `cross_module_calls`. For more information see [documentation for library(check)](https://www.swi-prolog.org/pldoc/man?section=check).

	Default value: `"errors": ["undefined", "trivial_fails", "format_errors", "redefined", "void_declarations"]`.

The [`args`](http://www.sublimelinter.com/en/latest/linter_settings.html#args) setting is empty by default, but linter uses options `-g *check program*` and `-t halt` for run check and stop execution.
