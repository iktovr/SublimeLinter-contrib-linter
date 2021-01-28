from SublimeLinter.lint import Linter, util
import re

SECTION_RE = re.compile(r'% Checking (?P<type>[\w/ ,]+) \.\.\.\r?\n'
                        r'(?P<errors>.*?)(?=% Checking)', re.DOTALL)
ERRORS_RE = re.compile(r'(?P<type>(?P<error>ERROR)|(?P<warning>Warning)): .+?:(?P<line>\d+):(?:(?P<col>\d+):)?'
                       r'(?:\r?\n(?P=type):)?\s+(?P<message>.*)')
UNDEFINED_RE = re.compile(r'(?P<error>Warning): (?P<message>(?:.+?)/\d+(?P<del>, which is referenced by'
                          r'(?:\r?\nWarning:\s+.+?:\d+:(?:\d+:)? .+)+))')
TRIVIAL_RE = re.compile(r'(?P<warning>Warning): (?P<message>(?:.+?)\(.*?\)(?P<del>, which is called from'
                        r'(?:\r?\nWarning:\s+.+?:\d+:(?:\d+:)? .+)+))')
LOCATION_RE = re.compile(r'Warning:\s+.+?:(?P<line>\d+):(?:(?P<col>\d+):)? .+')
FORMAT_RE = re.compile(r'(?P<error>Warning): .+?:(?P<line>\d+):(?:(?P<col>\d+):)? \r?\n'
                       r'Warning:\s+(?P<message>.*)')
REDEFINED_RE = re.compile(r'% (?P<near>.+?)(?P<arity>/\d+)\s+(?P<message>.+)')
VOID_DECL_RE = re.compile(r'(?P<warning>Warning): (?P<message>(?:.+?)/\d+ is declared as .+?, but has no clauses)')

ERRORS = {
    'consult':            "consult errors",
    'undefined':          "undefined predicates",
    'trivial_fails':      "trivial failures",
    'format_errors':      "format/2,3 and debug/3 templates",
    'redefined':          "redefined system and global predicates",
    'void_declarations':  "predicates with declarations but without clauses",
    'strings':            "strings",
    'rationals':          "rationals",
    'cross_module_calls': "cross module calls"
}

CHECK_PROGRAM = (
    'use_module(library(check)),'
    'Add={},'
    'setof([Pred,Msg], check:checker(Pred,Msg), All),'
    'subtract(All, Add, Del),'
    '(member([Pred,Msg], Del), retract(check:checker(Pred,Msg)), fail; true),'
    '(member([Pred,Msg], Add),'
    '(check:checker(Pred,Msg) -> fail; assert(check:checker(Pred,Msg))),'
    'fail; check)'
)

FIND_PROGRAM = (
    'current_predicate({}, Head),'
    'predicate_property(Head, line_count(X)),'
    'format(user_error, \"% ~d\", [X])'
)


class Swipl(Linter):
    cmd = None
    tempfile_suffix = '-'
    regex = None
    word_re = re.compile(r'^([:\-\w]+)')
    line_col_base = (1, 0)
    error_stream = util.STREAM_STDERR
    defaults = {
        'selector': 'source.prolog',
        'errors': ['undefined', 'trivial_fails', 'format_errors', 'redefined', 'void_declarations']
    }

    def cmd(self):
        errors = self.settings['errors']
        try:
            errors = set(errors)
        except TypeError:
            errors = {errors}
        errors -= {'consult'}
        errors = filter(lambda err: err in ERRORS, errors)
        program = CHECK_PROGRAM.format('[' + ','.join('[list_'+err+",'"+ERRORS[err]+"']" for err in errors) + ']')
        return ('swipl', '-g', program, '-t', 'halt', '${file}', '${args}')

    def find_errors(self, output):
        output = '% Checking {} ...\n'.format(ERRORS['consult']) + output + '% Checking'

        for section in SECTION_RE.finditer(output):
            err_type = section.group('type')
            errors = section.group('errors')

            if err_type == ERRORS['consult'] or \
               err_type == ERRORS['strings'] or \
               err_type == ERRORS['rationals'] or \
               err_type == ERRORS['cross_module_calls']:
                for match in ERRORS_RE.finditer(errors):
                    yield self.split_match(match, 'consult')

            elif err_type == ERRORS['undefined']:
                for match in UNDEFINED_RE.finditer(errors):
                    for location in LOCATION_RE.finditer(match.group('message')):
                        lmatch = self.split_match(match, 'undefined')
                        location = self.split_match(location)
                        lmatch['col'] = location.get('col', None)
                        lmatch['line'] = location['line']
                        yield lmatch

            elif err_type == ERRORS['trivial_fails']:
                for match in TRIVIAL_RE.finditer(errors):
                    for location in set(match.group('message').splitlines()):
                        lmatch = self.split_match(match, 'trivial_fails')
                        location = LOCATION_RE.search(location)
                        if location is None:
                            continue
                        location = self.split_match(location)
                        lmatch['col'] = location.get('col', None)
                        lmatch['line'] = location['line']
                        yield lmatch

            elif err_type == ERRORS['format_errors']:
                for match in FORMAT_RE.finditer(errors):
                    yield self.split_match(match, 'format_errors')

            elif err_type == ERRORS['redefined']:
                for match in REDEFINED_RE.finditer(errors):
                    yield self.split_match(match, 'redefined')

            elif err_type == ERRORS['void_declarations']:
                for match in VOID_DECL_RE.finditer(errors):
                    yield self.split_match(match, 'void_declarations')

    def find_clause(self, name):
        # type: (str) -> int
        """Return line number of the first clause of the predicate with given name."""
        cmd = ['swipl', '-g', FIND_PROGRAM.format(name), '-t', 'halt', '${file}']
        output = self.run(self.build_cmd(cmd), None)
        match = self.split_match(re.search(r'^% (?P<line>\d+)', output, re.M))
        if match is not None:
            return match['line']
        else:
            return 0

    def split_match(self, match, err_type=None):
        error = super().split_match(match)

        if err_type == 'consult':
            if error.get('col', None) is None:
                error['col'] = 0

        elif err_type == 'undefined':
            error['error'] = 'ERROR'
            error['message'] = 'Unknown procedure: ' + error['message'].replace(error['del'], '')

        elif err_type == 'trivial_fails':
            error['message'] = 'Trivial failure: ' + error['message'].replace(error['del'], '')

        elif err_type == 'format_errors':
            error['error'] = 'ERROR'

        elif err_type == 'redefined':
            line = self.find_clause(error['near'])
            error.update({'line': line,
                          'warning': 'Warning',
                          'message': error['message'] + ': ' + error['near'] + error['arity']})

        elif err_type == 'void_declarations':
            error.update({'line': 0})

        if (error.get('col', None) is not None):
            point = self.view.text_point(error['line'], 0)
            region = self.view.line(point)
            line = self.view.substr(region)
            if '\t' in line:
                swi_col = 0
                i = 0
                while i < error['col']:
                    if line[i] == '\t':
                        tab_size = 7 - swi_col % 8
                        error['col'] -= tab_size
                        swi_col += tab_size
                    i += 1
                    swi_col += 1

        return error
