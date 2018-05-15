class Error(Exception):
    pass


class CreationError(Error):
    def __init__(self, obj_type, obj_name, cft_prop, cft_value, err):
        self.object = {
            'type': obj_type,
            'name': obj_name
        }
        self.conflict = {
            'property': cft_prop,
            'value': cft_value
        }
        self.type = err
        self.message = self.generate_message()

    def generate_message(self):
        switcher = {
            'Exists': 'A {} with the {} "{}" already exists!'.format(
                self.object['type'],
                self.conflict['property'],
                self.conflict['value']),
            'Installed': ('The {} "{}" is already present on the {} "{}"!'
                          .format(self.conflict['property'],
                                  self.conflict['value'],
                                  self.object['type'],
                                  self.object['name'])),
            'ReqNotMet': ('The requirements to add the {} "{}" are not met!\n'
                          'These {} are missing:\n{}'
                          .format(self.object['type'],
                                  self.object['name'],
                                  self.conflict['property'],
                                  '\n'.join(self.conflict['value']))),
            'NotInstalled': ('The {} "{}" is not installed on the {} "{}"!'
                             .format(self.conflict['property'],
                                     self.conflict['value'],
                                     self.object['type'],
                                     self.object['name'])),
            'NotSupported': ('The "{}" {} is not supported for the {} "{}"!'
                             .format(self.conflict['value'],
                                     self.conflict['property'],
                                     self.object['type'],
                                     self.object['name'])),
            'Dependency': ('Cannot delete the {} "{}" because it is required '
                           'for these {} installed:\n - {}'
                           .format(self.object['type'],
                                   self.object['name'],
                                   self.conflict['property'],
                                   '\n - '.join(self.conflict['value']))),
            'MaxNumber': ('The maximum number of {} "{}" is already installed '
                          'on the {} "{}".\nRemove one "{}" before installing'
                          ' a new one.'.format(self.conflict['property'],
                                               self.conflict['value'],
                                               self.object['type'],
                                               self.object['name'],
                                               self.conflict['value'])),
            'TooManyHA': ('This operation is switching the {} "{}" in '
                          'High Availability mode.\nSome components intalled'
                          ' are not compatible with this mode.\n'
                          'Remove the following {} to switch to High '
                          'Availability mode:\n - {}'
                          .format(self.object['type'],
                                  self.object['name'],
                                  self.conflict['property'],
                                  '\n - '.join(self.conflict['value'])))
        }

        return switcher.get(self.type, self.type)


class LoadError(Error):
    def __init__(self, obj_type, obj_name, err):
        self.object = {
            'type': obj_type,
            'name': obj_name
        }
        self.type = err
        self.message = self.generate_message()

    def generate_message(self):
        switcher = {
            'NotExist': 'The {} "{}" doesn\'t exist!'.format(
                self.object['type'],
                self.object['name']),
            'NoContext': ('No cluster specified nor managed! Use "--cluster" '
                          'to specify a cluster.'),
            'MustExit': ('You are currently managing the cluster "{}". '
                         'Type "exit" to manage other clusters.'.format(
                             self.object['name'])),
            'NoConfFile': ('Couldn\'t find the file "jumbo_config" for cluster'
                           ' "{}".\nAll cluster configuration has been lost.'
                           .format(self.object['name']))
        }
        return switcher.get(self.type, self.type)
