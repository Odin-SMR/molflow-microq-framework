// Test helper functions


// Tests of custom equality functions:
describe("Custom equality functions:", function() {

    it("almost_equal should be true if numbers are within 1e-9", function() {
        expect(almost_equal(1, 1)).toBe(true);
        expect(almost_equal(0, 1e-9)).toBe(true);
        expect(almost_equal(0, 1e-8)).toBe(false);
    });

    it("arrays_almost_equal should be true if all elements are almost_equal",
            function() {
        expect(arrays_almost_equal([1, 0], [1.0, 1e-9])).toBe(true);
        expect(arrays_almost_equal([1, 0], [1.0, 1e-8])).toBe(false);
    });

});
