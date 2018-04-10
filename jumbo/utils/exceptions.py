class Error(Exception):
    pass


class CreationError(Error):
    def __init__(self, obj_type, obj_name, cft_type, cft_value):
        self.object = {
            'type': obj_type,
            'name': obj_name
        }
        self.conflict = {
            'type': cft_type,
            'value': cft_value
        }
        self.message = 'A {} with the {} `{}` already exists!'.format(
            self.object['type'],
            self.conflict['type'],
            self.conflict['value'])


class LoadError(Error):
    def __init__(self, obj_type, obj_name, err):
        self.object = {
            'type': obj_type,
            'name': obj_name
        }
        self.message = self.generate_message(err)
        self.type = err

    def generate_message(self, err):
        switcher = {
            'NotExist': 'The {} `{}` doesn\'t exist!'.format(
                self.object['type'],
                self.object['name']),
            'NoContext': ('No cluster specified nor managed! Use "--cluster" '
                          'to specify a cluster.'),
            'MustExit': ('You are currently managing the cluster `{}`. '
                         'Type "exit" to manage other clusters.'.format(
                             self.object['name'])),
            'NoConfFile': ('Couldn\'t find the file `jumbo_config` for cluster'
                           ' `{}`\nAll cluster configuration has been lost.'
                           .format(self.object['name']))
        }
        return switcher.get(err, err)
