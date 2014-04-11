def readme():
    """
    Returns contents of README.md

    @return - String

    """
    with open('README.md') as f:
        return f.read()
