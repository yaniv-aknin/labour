from __future__ import print_function

def trivial_report(statistics):
    print("\nTest complete.")
    success_percentage = float(statistics.successes) / statistics.total_requests * 100
    failure_percentage = float(statistics.failures) / statistics.total_requests * 100
    print("Total requests sent: %d (%d (%.2f%%) returned OK and %d (%.2f%%) had some failure." %
           (statistics.total_requests, statistics.successes, success_percentage, statistics.failures, failure_percentage))
    print()
    if statistics.failures:
        print("Failure Breakdown:")
        for status, amount in statistics.response_histogram.iteritems():
            print("Code: %s\tCount: %d\tPercentage: %.2f%%" % (status, amount, float(amount) / statistics.failures * 100))
