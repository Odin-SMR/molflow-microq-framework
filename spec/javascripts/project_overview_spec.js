// Tests for project_overview.js


// Pretty printing objects:
describe("Function for creating list from an object:", function() {

    it("objectAsList should take an object and return an HTML list",
            function() {
        arr = {
            "foo": "bar",
            "ans": 42
        };
        result = "<ul><li>foo: bar</li><li>ans: 42</li></ul>";

        expect(objectAsList(arr)).toEqual(result);
    });

});
