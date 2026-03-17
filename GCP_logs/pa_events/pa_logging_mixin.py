# encoding: utf-8

import os
import json
import codecs
import datetime
from pprint import pformat
from rich import print_json

UPDATE_PERIOD = 10
LOG_PAYLOAD = True


def ensure_path_exists(path,
                       includes_filename=True):
    if not path:
        return

    if includes_filename:
        # Discard filename
        path, _ = os.path.split(path)

    if not os.path.exists(path):
        os.makedirs(path)


class ProductAnalyticsLoggingMixin(object):

    def __init__(self):
        self.ensure_log_paths_exist()
        self.minimise_log_files()

    @property
    def log_files(self):
        raise NotImplementedError('Should be overridden in subclass')

    def ensure_log_path_exists(self,
                               path):
        try:
            ensure_path_exists(path)
        except Exception as e:
            print(self.format_log("Exception: {es}".format(es=str(e))))
            print('Log folder could not be accessed for {path}'.format(path=path))

    def ensure_log_paths_exist(self):
        [self.ensure_log_path_exists(log_file) for log_file in self.log_files]

    def minimise_log_file(self,
                          log_file):
        today_start_string = self.format_log(text='').split(' ')[0]
        try:
            with codecs.open(log_file,
                             'r',
                             encoding='utf-8') as lf:
                lines = lf.read().splitlines()
            for line_number, line in enumerate(lines):
                if line.startswith(today_start_string):
                    break
            lines.append('')
            with codecs.open(log_file,
                             'w',
                             encoding='utf-8') as lf:
                lf.write('\n'.join(lines[line_number:]))

        except Exception as e:
            print(self.format_log("Exception: {es}".format(es=str(e))))
            print('Error minimising log file {log_file}'.format(log_file=log_file))

    def minimise_log_files(self):
        [self.minimise_log_file(log_file) for log_file in self.log_files]

    def format_log(self,
                   text):
        try:
            return (u"{d:%Y-%m-%d %H:%M:%S} | {t}"
                    .format(d=datetime.datetime.now(),
                            # t=text.decode('utf-8')))
                            t=text))
        except UnicodeDecodeError as e:
            return self.format_log(text=''.join([c if ord(c) < 128 else ord(c) for c in text]))

    def log(self,
            text,
            format_all_lines=True,
            file=True,
            screen=True,):
        try:
            try:
                lines = text.splitlines()
            except AttributeError:
                lines = text
            if format_all_lines:
                lines = [self.format_log(line) for line in lines]
            else:
                lines = [self.format_log('')] + lines

            if screen:
                for line in lines:
                    print(line)

            if file:
                for log_file in self.log_files:
                    try:
                        with codecs.open(log_file,
                                         'a',
                                         encoding='utf-8') as lf:
                            for line in lines:
                                lf.write(line + u'\n')
                    except Exception as e:
                        print(self.format_log(e))
                        print(self.format_log("Warning: Failed to write to log file: {lf}".format(lf=log_file)))
        except Exception as e:
            print(self.format_log(e))
            print(self.format_log("Warning: Logging error"))

    def log_json(self,
                 json_dict,
                 file=True,
                 screen=True,):
        if file:
            self.log(json.dumps(json_dict,
                                indent=4,
                                ensure_ascii=False),
                     file=file,
                     screen=False)
        if screen:
            try:
                print(self.format_log(''))
                print_json(data=json_dict,
                           indent=4)
            except Exception as e:
                print(self.format_log(e))
                print(self.format_log("Warning: Logging error"))


class ProductAnalyticsLoggingMixinTest(ProductAnalyticsLoggingMixin):

    @property
    def log_files(self):
        return ['logs/test_logging_mixin.log']

    def _init__(self):
        super(ProductAnalyticsLoggingMixinTest, self).__init__()


if __name__ == "__main__":
    blah = ProductAnalyticsLoggingMixinTest()
    blah.log('test')
