'use strict';
var cleanCSS = require('gulp-clean-css');
var gulp = require('gulp');
var gulpif = require('gulp-if');
var sass = require('gulp-sass');
var autoprefixer = require('gulp-autoprefixer');
var paths = require('../paths');
var argv = require('yargs').argv;


var isProduction = process.env.NODE_ENV === 'production';
if (argv.production) {
    isProduction = true;
}


/**
 * scss task
 * Run using "gulp scss"
 * Searches for sass files in paths.sassSrc
 * Compiles sass to css
 * Auto prefixes css
 * Writes css to paths.cssDir
 */
function scss() {
    // Searches for sass files in paths.sassSrc
    return gulp.src(paths.sassSrc)
        // Compiles sass to css
        .pipe(sass({
            outputStyle: isProduction ? 'compressed' : 'expanded',

            // Allow importing from node_modules in .scss files
            includePaths: 'node_modules/',
        })
            .on('error', sass.logError))

        // Auto prefixes css
        .pipe(autoprefixer({
            browsers: ['last 2 versions', 'ie 11'],
            cascade: false
        }))

        // Remove duplicated code
        .pipe(gulpif(isProduction, cleanCSS({level: 2})))

        // Writes css to paths.cssDir
        .pipe(gulp.dest(paths.cssDir));
};


gulp.task('sass', scss);
gulp.task('scss', scss);
exports.scss = scss;
exports.scss = scss;
