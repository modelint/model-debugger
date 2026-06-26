"""
exceptions.py – Model Execution exceptions
"""

class MDBException(Exception):
    """ Model Debugger exception """
    pass

class MDBScenarioException(MDBException):
    """ Error encountered due to bad mdb/user input in scenario input"""
    pass