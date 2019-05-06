// Karma configuration
// Generated on Tue May 30 2017 17:11:30 GMT+0200 (CEST)
//
module.exports = (config) => {
    config.set({

        // base path that will be used to resolve all patterns (eg. files, exclude)
        basePath: '',

        // frameworks to use
        // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
        frameworks: ['jasmine'],


        // list of files / patterns to load in the browser
        files: [
            { pattern: 'src/uservice/core/static/js/jquery.js', watched: false },
            { pattern: 'src/uservice/core/static/js/moment/moment.js', watched: false },
            { pattern: 'src/uservice/core/static/js/project_overview.js', watched: false },
            { pattern: 'spec/javascripts/helpers/*.js', watched: false },
            { pattern: 'spec/javascripts/*.js', watched: false }
        ],


        // list of files to exclude
        exclude: [
            '**/*.swp',
        ],


        // test results reporter to use
        // possible values: 'dots', 'progress'
        // available reporters: https://npmjs.org/browse/keyword/karma-reporter
        reporters: ['dots', 'coverage', 'junit'],


        // web server port
        port: 9876,


        // enable / disable colors in the output (reporters and logs)
        colors: true,


        // level of logging
        // possible values: config.LOG_DISABLE || config.LOG_ERROR ||
        //  config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
        logLevel: config.LOG_INFO,


        // enable / disable watching file and executing tests whenever any file changes
        autoWatch: true,


        // start these browsers
        // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
        browsers: ['ChromeHeadless'],

        browserNoActivityTimeout: 30000,

        // Continuous Integration mode
        // if true, Karma captures browsers, runs the tests and exits
        singleRun: false,

        // Concurrency level
        // how many browser should be started simultaneous
        concurrency: Infinity,

        coverageReporter: {
            type: 'cobertura',
            dir: '.',
            file: 'coverage.xml',
        },
    });
};
