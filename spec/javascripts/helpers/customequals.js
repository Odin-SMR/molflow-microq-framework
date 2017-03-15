// Custom equality functions for Jasmine.
//
// A custom equality function should take two arguments and return
// true/false iff. both are of comparable type and are equal/unequal
// according to the custom measure.
//
// To use a custom equality, add register it with Jasmine before the
// tests in a describe context by:
//    beforeEach(function() {
//        jasmine.addCustomEqualityTester(myFirstCustomEquals);
//        jasmine.addCustomEqualityTester(mySecondCustomEquals);
//    });
// This should be done in each describe in order to make sure the
// custom equals are only used within the correct scope.


function almost_equal(first, second) {
    if (typeof first == "number" && typeof second == "number") {
        return Math.abs(first - second) <= 1e-9;
    }
}


function arrays_almost_equal(first, second) {
    if (Array.isArray(first) && Array.isArray(second) &&
            first.length == second.length) {
        for (var i=0; i < first.length; i++) {
            if (!almost_equal(first[i], second[i])) {
                return false;
            }
        }
        return true;
    }
}
