#############################################################
# Add performance tests to ctest
#############################################################

IF (NOT QMC_DATA)
  MESSAGE("QMC_DATA is not set. Performance tests will be skipped.")
ELSE()
  message("Adding performance tests for QMCPACK")
ENDIF()

# includes 
SUBDIRS(NiO C-graphite C-molecule)

