class Pam(dict):
    """
    Pam credentials model for salt. Just a dictionary.
    """

    def __init__(self, username, password):
        """
        Constructor

        @param username - String username
        @param password - String password

        """
        self.update({'eauth': 'pam',
                     'username': username,
                     'password': password})
