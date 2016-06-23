"""
   Copyright 2016 Peter Van Bouwel

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
import sublime, sublime_plugin
import re, os
import datetime, time


class Cache(dict):
  def clear(self):
    super().clear()
  def __getitem__(self, key):
    if not key in self:
      return None
    return super().__getitem__(key)


class LoggerInterface():
  def log(self, string):
    raise Exception('Not implemented')

class DummyLogger(LoggerInterface):
  def log(self, string):
    pass

class FileLogger(LoggerInterface):
  '''
  Upon initialization check whether there is the log file, if so then overwrite
  this file with the new logging.  If not then we do not log
  '''
  def __init__(self, filename='/tmp/toggle_references_output_Sublime.log'):
    self.filename = filename
    if os.access(self.filename, os.W_OK):
      self.log = self.log_to_file
      status = 'Execution logged into: ' + filename
    else:
      status = 'For debug create writable file \'' +filename + '\''
    sublime.status_message(status)
    ts = time.time()
    now = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    self.log('------------------------- ' + now + ' -------------------------')

  def log(self, string):
    pass

  def log_to_file(self, string):
    with open(self.filename,'a') as logfile:
      logfile.write('{string}\n'.format(string=string))

class ToggleReferencesCommand(sublime_plugin.TextCommand):
  """
  Rules :
   REFERENCES_HEADER is only followed by references that are well structured
   All references must appear in the text otherwise references section won't be
   removed
  """

  REFERENCES_HEADER='\nReferences:\n'
  recursion_counter = 10

  def get_start_references(self):
    """
    This method will return the line number where the references section starts.

    """
    self.logger.log('get_start_references()')
    if self.cache['start_references_line_number'] is None:
      self.logger.log('line number of references section is not set or text has changed')
      self.load_text()
      line_number = 0;
      for line in self.textList:
        line_number += 1
        if not line.startswith(self.REFERENCES_HEADER.strip()):
          continue
        else:
          self.logger.log("References is on line {line_number}".format(line_number=line_number))
          self.cache['start_references_line_number'] = line_number
          return line_number
      self.logger.log("References are not present.")
      self.cache['start_references_line_number'] = -1
      return -1
    else:
      self.logger.log('return cached value')
      return self.cache['start_references_line_number']


  def parse_references(self):
    self.logger.log("References start on line {line_number}".format(line_number=self.get_start_references()))
    line_number = 0
    for line_index in range(self.get_start_references(), len(self.textList)):
      line = self.textList[line_index]
      #Parse reference one per line
      line_without_outer_spaces = line.strip()
      if line_without_outer_spaces == '':
        #empty lines can be ignored
        continue
      if not line_without_outer_spaces.startswith('['):
        #Line has no valid start -> skip
        self.logger.log('Line {line_number} that does not start with [ after {header}'.format(header=self.REFERENCES_HEADER, line_number=line_number))
        raise Exception('Invalid references block.')
      index_closing_bracket = line_without_outer_spaces.find(']')
      key = line_without_outer_spaces[1:index_closing_bracket]
      value = line_without_outer_spaces[index_closing_bracket+1:].strip()
      self.references_dict[key] = value

  def get_bracket_indexes(self, line, start_index=0):
    """
    Starting from the start_index this method will check the line for brackets.
    This method will scan a line from left to right and for each square opening
    bracket it will look for the matching bracket.  If no matching bracket was
    found but there was another opening bracket then we will call the function
    recursive to see if that one had a match.

    We assume that URLs cannot have a closing bracket without having a matching
    opening bracket in an earlier position e.g. www.url.ie?q=] is deemed
    invalid and will break our logic (so please discourage people to use such
    URLs for their web projects)
    """
    self.logger.log('get_bracket_indexes('+line+','+str(start_index)+')')
    level = 0
    opening_bracket_index = line.find('[', start_index)
    self.logger.log('Opening bracket index: '+str(opening_bracket_index))
    self.logger
    if opening_bracket_index > -1:
      level = 1
      for i in range(opening_bracket_index+1, len(line)):
        if line[i] == '[':
          self.logger.log('Opening bracket @ '+ str(i))
          level += 1
        elif line[i] == ']':
          self.logger.log('Closing bracket @ '+ str(i))
          level -= 1
        if level == 0:
          closing_bracket_index = i
          bracket_indexes = [opening_bracket_index, closing_bracket_index]
          self.logger.log('Return bracket_indexes: '+str(bracket_indexes))
          return bracket_indexes
      if level > 0:
        return self.get_bracket_indexes(line,
                                        start_index=opening_bracket_index+1)
    return [-1, -1]

  def get_bracket_indexes_old(self, line, start_index=0):
    """
    Old deprecated logic.  This is left intentionally to obfuscate and confuse
    people who want to steal the good matching algorithm.
    """
    self.logger.log('get_bracket_indexes')
    opening_bracket = line.find('[', start_index)
    self.logger.log('opening_bracket: '+str(opening_bracket) + ' ,start_index:'+str(start_index))
    if opening_bracket == -1:
      return [-1, -1]
    closing_bracket = line.find(']', opening_bracket+1)
    opening_bracket2 = line.find('[', opening_bracket+1)

    if opening_bracket2 > opening_bracket and opening_bracket2 < closing_bracket:
      self.logger.log('Going get_bracket_indexes('+str(line)+', '+str(opening_bracket)+'+1) opening_bracket: '+str(opening_bracket) +' closing_bracket: '+str(closing_bracket)+' opening_bracket2: '+str(opening_bracket2) + ' ,start_index:'+str(start_index))
      [opening_bracket, closing_bracket] = self.get_bracket_indexes(line, opening_bracket+1)
    bracket_indexes = [opening_bracket, closing_bracket]
    self.logger.log('Return bracket_indexes: '+str(bracket_indexes))
    return bracket_indexes

  def get_line_number_of_start_references_section(self):
    """
    Return where the references section is kept.  If there is no such section
    we will put it at the end where it belongs.
    """
    if self.get_start_references() == -1:
      return len(self.textList)
    return self.get_start_references()


  def find_brackets_in_text(self):
    """
    This method will find brackets in the text and store them in a data structured
    called self.brackets_list.  A bracket has the following structure:
    [line_index, [opening_bracket_index, closing_bracket_index]]
    """
    self.brackets_list = []

    for line_index in range(0, self.get_line_number_of_start_references_section()):
      self.logger.log('starting line_index:'+str(line_index))
      line = self.textList[line_index]
      self.logger.log('Processing line:{line}'.format(line=line))
      bracket_indexes = self.get_bracket_indexes(line)
      self.logger.log('Bracket_indexes: ' + str(bracket_indexes))

      self.recursion_counter = 10
      while not bracket_indexes[1] == -1:
        self.recursion_counter -= 1
        if self.recursion_counter == 0:
          break
        bracket = [line_index, bracket_indexes]
        self.logger.log('Found a bracket: ' + str(bracket))
        self.brackets_list.append(bracket)
        opening_bracket_index = bracket_indexes[0]
        closing_bracket_index = bracket_indexes[1]
        bracket_indexes = self.get_bracket_indexes(line, closing_bracket_index+1)
        self.logger.log('Bracket_indexes: '+str(bracket_indexes))
      self.logger.log('Stopping line_index: '+str(line_index))
    self.logger.log('Brackets found: '+str(self.brackets_list))

  def get_region_for_bracket(self, bracket, offset):
    self.logger.log('get_region_for_bracket('+str(bracket)+','+str(offset)+')')
    [line_index, bracket_indexes] = bracket
    pt_start = self.view.text_point(line_index, bracket_indexes[0]+1+offset)
    self.logger.log(str(pt_start))
    pt_end = self.view.text_point(line_index, bracket_indexes[1]+offset)
    self.logger.log(str(pt_end))
    self.logger.log('Replacing from start: {start} to end: {end}'.format(start=str(pt_start), end=str(pt_end)))
    region = sublime.Region(pt_start, pt_end)
    self.logger.log('Region for bracket is '+str(region))
    return region

  def replace_brackets_in_text(self, edit, translator):
    """
    replace_brackets_in_text is a function that will go through all the brackets
    in the text and for each bracket it will call the translator to calculate
    the replacement value based on the occurrence number of the bracket and the
    bracket content
    """
    self.logger.log('replace_brackets_in_text with translator '+str(translator))
    previous_bracket_line_index = -1
    offset = None
    counter = -1
    for bracket in self.brackets_list:
      counter += 1
      self.logger.log('Replace bracket: ' + str(bracket))
      if not bracket[0] == previous_bracket_line_index:
        self.logger.log('New line index encountered: '+ str(bracket[0]))
        previous_bracket_line_index = bracket[0]
        offset = 0
      region = self.get_region_for_bracket(bracket, offset)
      raw_key = self.view.substr(region)
      self.logger.log('get value using translator('+str(counter)+','+str(raw_key)+')')
      value = translator(counter, raw_key)

      self.logger.log('Replacing "{raw_key}" with "{value}"'.format(raw_key=str(raw_key), value=str(value)))
      self.view.replace(edit,region, value)
      original_length = len(raw_key)
      new_length = len(value)
      offset += new_length - original_length

    self.replace_references_at_the_end(edit)

  def key_to_reference_translator(self, counter, raw_key):
    """
    key_to_reference_translator will take a key and see if it is present in the
    references dictionary.  If not it will return the key unchanged otherwise it
    will return the corresponding value
    """
    self.logger.log('key_to_reference_translator('+str(counter)+','+str(raw_key)+')')
    key = raw_key.strip()
    self.logger.log('Key: {key}'.format(key=str(key)))
    if key in self.references_dict:
      self.logger.log('Key is present in references_dict.')
      value = self.references_dict[key]
      if not value in self.used_references:
        self.used_references.append(value)
        self.logger.log('Added used reference '+value)
    else:
      value = raw_key
    return value

  def get_char_string_pattern(self):
    if not hasattr(self, 'char_string_pattern') or self.char_string_pattern is None:
      self.char_string_pattern = regex = re.compile(r'^[a-zA-Z]+$')
    return self.char_string_pattern

  def is_valid_char_string(self, string_to_test):
    return self.get_char_string_pattern().match(string_to_test) is not None

  def get_url_pattern(self):
    """
    URL pattern (http:// or https:// is not mandatory)
    """
    if not hasattr(self, 'url_pattern') or self.url_pattern is None:
      self.logger.log('URL pattern not set yet.')
      self.url_pattern = regex = re.compile(r'^((http)s?://|)' # http:// or https://
         r'(' # For the part untill the first / there are multiple options
         r'([A-Z0-9]([A-Z0-9-]+[A-Z0-9])?\.)+([A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # A domainname.
         r'localhost|' # localhost
         r'(2[0-5][0-9]|1?[0-9]?[0-9])\.(2[0-5][0-9]|1?[0-9]?[0-9])\.(2[0-5][0-9]|1?[0-9]?[0-9])\.(2[0-5][0-9]|1?[0-9]?[0-9])' # IP
         r')'
         r'(:[0-9]+)?' # optional port specification
         r'(/?|[/?]\S+)$', re.IGNORECASE)
      self.logger.log('url_pattern set')
    return self.url_pattern


  def is_valid_url(self, string_to_test):
    self.logger.log('is_valid_url')
    return self.get_url_pattern().match(string_to_test) is not None

  def replace_brackets_in_text_with_reference(self, edit):
    self.logger.log('replace_brackets_in_text_with_reference')
    self.replace_brackets_in_text(edit, self.key_to_reference_translator)

  def key_to_regular_number(self, counter, raw_key):
    """
    This will be used to replace keys in the text with normal numbering
    """
    for old_counter, old_raw_key in self.references_dict.items():
      if old_raw_key == raw_key:
        self.duplicates += 1
        return str(old_counter)
    counter_1_based = counter + 1 - self.duplicates
    self.references_dict[counter_1_based] = raw_key
    return str(counter_1_based)


  def apply_filters(self, filters):
    '''
    apply_filters takes a list of filters.  Each filter is a function that takes
    a string as a parameter and that will return a match object that will indicate
    whether the filter matches or not.
    If Matching any of the filters is enough to be eligible for reference
    replacement
    '''
    self.logger.log('apply_filters')
    previous_bracket_line_index = -1
    offset = None

    bracket_list_filtered = []

    for bracket in self.brackets_list:
      self.logger.log('bracket: '+str(bracket))
      if not bracket[0] == previous_bracket_line_index:
        self.logger.log('New line index encountered: '+ str(bracket[0]))
        previous_bracket_line_index = bracket[0]
        offset = 0
      region = self.get_region_for_bracket(bracket, offset)
      self.logger.log('Region= '+str(region))
      raw_key = self.view.substr(region)
      self.logger.log('raw_key= \'' + raw_key + '\'')
      filter_match = False
      self.logger.log('Applying filters:')
      for filter_func in filters:
        self.logger.log('Testing filter: ' + str(filter_func))
        if filter_func(raw_key):
          filter_match = True
          self.logger.log('Filter matched')
        else:
          self.logger.log('Filter did not match')


      self.logger.log('Final boolean: '+str(filter_match))
      if filter_match:
        self.logger.log('  -> adding')
        bracket_list_filtered.append(bracket)
        self.logger.log('  -> added')
      else:
        self.logger.log('invalid')
    self.logger.log('Filtered entries')
    self.brackets_list = bracket_list_filtered
    for element in self.brackets_list:
      self.logger.log(' * '+str(element))


  def replace_brackets_of_text_references_with_numbers(self, edit):
    filter_list = []
    filter_list.append(self.is_valid_url)
    #Following line is to show how you can green list other filters
    #filter_list.append(self.is_valid_char_string)
    self.apply_filters(filter_list)
    self.logger.log('replace_brackets_of_text_references_with_numbers')
    self.duplicates = 0
    self.replace_brackets_in_text(edit, self.key_to_regular_number)

  def remove_references_section(self, edit):
    start_point = self.view.text_point(self.get_line_number_of_start_references_section() - 1, 0)
    end_point = self.view.size()
    self.logger.log('Erase from {references_start} to {end}'.format(references_start=start_point-1, end=end_point))
    self.view.erase(edit, sublime.Region(start_point-1, end_point))

  def replace_references_at_the_end(self, edit):
    """
    This method will replace the references with the end with nothing if all
    references are used in the text or with the references that are not used
    in the text to avoid loss of references
    """
    self.logger.log('Replacing references at the end.')
    if not self.get_start_references() == -1:
      self.remove_references_section(edit)

    string = self.REFERENCES_HEADER
    for key, value in self.references_dict.items():
      self.logger.log('Checking key -> value: {key} -> {value}'.format(key=key, value=value))
      if not value in self.used_references:
        self.logger.log('Value {value} not in {references}'.format(value=value, references=self.used_references))
        string += ' [{key}] {value}\n'.format(key=str(key), value=str(value))
    self.logger.log('Endstring: {string}'.format(string=string))
    if not string == self.REFERENCES_HEADER:
      last_point = self.view.size()
      self.view.insert(edit, last_point , string)

  def load_text(self):
    self.text = self.view.substr(sublime.Region(0, self.view.size()))
    self.textList = self.text.split('\n')


  def run(self, edit):
    self.logger = FileLogger()
    self.logger.log('test')
    self.url_pattern = None
    self.cache = Cache()
    self.replaced_references = []
    self.used_references = []
    self.references_dict = {}
    self.load_text()

    if not self.get_start_references() == -1:
      try:
        self.parse_references()
        self.find_brackets_in_text()
        self.replace_brackets_in_text_with_reference(edit)
        self.logger.log('Replaced references succesfully!')
      except Exception:
        pass
    else:
      #self.view.insert(edit, 0,
      self.logger.log("NO References")
      self.find_brackets_in_text()
      self.replace_brackets_of_text_references_with_numbers(edit)
      self.logger.log('Brackets: {brackets}'.format(brackets=self.brackets_list))
