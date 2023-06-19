# InkReveal

## Installation

I recommend using the latest version of Inkscape: https://inkscape.org/release/inkscape-1.2.2/

To install the extension:
First, locate the extension folder of Inkscape via **Edit ‣ Preferences ‣ System: User extensions**.
Then, copy this repository into the extension folder and restart Inkscape.

The extension is installed if the `Save as...` options include the type `Reveal.js presentation (*.html)`

## Usage

To create a presentation out of your current file, save your document as a `Reveal.js presentation (*.html)`.

This will create a `.html` file that contains a [reveal.js](https://revealjs.com/) presentation created from the layers of your document.

### Generation of slides

The rules for generating a slide are relatively simple:

Each top-level layer represents a new slide. In addition, each direct sublayer or subgroup of the 
the document represents an element that will appear one after the other. See the folder `examples` for an example presentation.
