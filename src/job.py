import logging

logger = logging.getLogger( __name__ )

class Job( object ):
    """
    A class encapsulating state about a jobTree job including its child commands and follow-on commands.

    Note that a parent Job instance does not store its children as instances of the Job class but
    uses 3-tuples of the form (jobStoreId, memory, cpu) instead.
    """

    @staticmethod
    def create( command, memory, cpu, tryCount, jobStoreID, logJobStoreFileID ):
        return Job(
            remainingRetryCount=tryCount,
            jobStoreID=jobStoreID,
            followOnCommands=[ (command, memory, cpu, 0) ],
            messages=[ ],
            logJobStoreFileID=logJobStoreFileID )

    def __init__( self, remainingRetryCount, jobStoreID,
                  children=None, followOnCommands=None, messages=None, logJobStoreFileID=None ):
        self.remainingRetryCount = remainingRetryCount
        self.jobStoreID = jobStoreID
        # TODO: Consider using a set for children
        self.children = children or [ ]
        self.followOnCommands = followOnCommands or [ ]
        self.messages = messages or [ ]
        self.logJobStoreFileID = logJobStoreFileID

    def setupJobAfterFailure( self, config ):
        if len( self.followOnCommands ) > 0:
            self.remainingRetryCount = max( 0, self.remainingRetryCount - 1 )
            logger.critical( "Due to failure we are reducing the remaining retry \
            count of job %s to %s" % (self.jobStoreID, self.remainingRetryCount) )
            # Set the default memory to be at least as large as the default, in
            # case this was a malloc failure (we do this because of the combined
            # batch system)
            self.followOnCommands[ -1 ] = (self.followOnCommands[ -1 ][ 0 ], \
                max( self.followOnCommands[ -1 ][ 1 ],
                     float( config.attrib[ "default_memory" ] ) )) + \
                                          self.followOnCommands[ -1 ][ 2: ]
            logger.critical( "We have set the default memory of the failed job to %s bytes" \
                             % self.followOnCommands[ -1 ][ 1 ] )
        else:
            logger.critical( "The job %s has no follow on jobs to reset" % self.jobStoreID )

    def clearLogFile( self, jobStore ):
        """Clears the log file, if it is set.
        """
        if self.logJobStoreFileID is not None:
            jobStore.deleteFile( self.logJobStoreFileID )
            self.logJobStoreFileID = None

    def setLogFile( self, logFile, jobStore ):
        """Sets the log file in the file store. 
        """
        if self.logJobStoreFileID is not None:  # File already exists
            jobStore.updateFile( self.logJobStoreFileID, logFile )
        else:
            self.logJobStoreFileID = jobStore.writeFile( self.jobStoreID, logFile )
            assert self.logJobStoreFileID is not None

    def getLogFileHandle( self, jobStore ):
        """
        Returns a context manager that yields a file handle to the log file
        """
        return jobStore.readFileStream( self.logJobStoreFileID )

    # Serialization support methods

    def toList( self ):
        """
        Deprecated. Use toDict() instead.
        """
        return [
            self.remainingRetryCount,
            self.jobStoreID,
            self.children,
            self.followOnCommands,
            self.messages,
            self.logJobStoreFileID ]

    @staticmethod
    def fromList( l ):
        """
        Deprecated. Use fromDict() instead.
        """
        return Job( *l )

    def toDict( self ):
        return self.__dict__.copy( )

    @staticmethod
    def fromDict( d ):
        return Job( **d )
    
    def __hash__( self ):
        return hash( self.jobStoreID )

    def __eq__( self, other ):
        return (
            isinstance( other, self.__class__ )
            and self.remainingRetryCount == other.remainingRetryCount
            and self.jobStoreID == other.jobStoreID
            and set( self.children ) == set( other.children )
            and self.followOnCommands == other.followOnCommands
            and self.messages == other.messages
            and self.logJobStoreFileID == other.logJobStoreFileID )

    def __ne__( self, other ):
        return not self.__eq__( other )
    
    def __repr__( self ):
        return 'Job( **%r )' % self.__dict__
