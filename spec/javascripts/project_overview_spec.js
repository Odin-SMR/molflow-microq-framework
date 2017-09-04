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

describe("Javascript datetime comparison", function() {

    it("returns true if a given datetime comes before another given datetime",
            function() {
        date1 = "2001-01-01T12:00:00Z";
        date2 = "2001-01-01T13:00:00Z";

        expect(compareTwoDates(date1, date2)).toEqual(true);
    });
    it("returns false otherwise",
            function() {
        date1 = "2001-01-01T12:00:00Z";
        date2 = "2001-01-01T13:00:00Z";

        expect(compareTwoDates(date2, date1)).toEqual(false);
    });

});


describe("Javascript job duration calculator", function() {

    it("calculates duration between claimed and failed",
            function() {
        Claimed = "2001-01-01T12:00:00Z";
        Failed = "2001-01-01T12:00:06Z";
        Finished = null;

        expect(getDuration(Claimed, Finished, Failed)).toEqual("6s");
    });

    it("calculates duration between claimed and finished",
            function() {
        Claimed = "2001-01-01T12:00:00Z";
        Failed = null;
        Finished = "2001-01-01T12:00:06Z";

        expect(getDuration(Claimed, Finished, Failed)).toEqual("6s");
    });

    it("understand that duration can not ne negative",
            function() {
        Claimed = "2001-01-01T12:00:00Z";
        Failed = "1999-01-01T12:00:06Z";
        Finished = null;

        expect(getDuration(Claimed, Finished, Failed)).toEqual("<i>N/A</i>");
    });

});

