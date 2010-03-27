from __future__ import print_function

def trivial_report(used_driver):
    print("\nTest complete.")
    total_requests = used_driver.successes + used_driver.failures
    success_percentage = float(used_driver.successes) / total_requests * 100
    failure_percentage = float(used_driver.failures) / total_requests * 100
    print("Total requests sent: %d (%d (%.2f%%) returned OK and %d (%.2f%%) had some failure." %
           (total_requests, used_driver.successes, success_percentage, used_driver.failures, failure_percentage))
    print()
    if used_driver.failures:
        print("Failure Breakdown:")
        for status, amount in used_driver.received_statuses.iteritems():
            print("Code: %s\tCount: %d\tPercentage: %.2f%%" % (status, amount, float(amount) / used_driver.failures * 100))
