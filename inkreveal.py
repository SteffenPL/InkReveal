import os 
import zipfile
import shutil
import re

from copy import deepcopy

from lxml import etree


reveal_js_path = "reveal.js-master"

import inkex 

class RevealExporter(inkex.OutputExtension):
    def add_arguments(self, parser):
        parser.add_argument("--tab")
        parser.add_argument("--dir")
        parser.add_argument("--template")
        parser.add_argument("--install_revealjs")

    def validate_inputs(self):
        pass

    def generate_slides(self, slides_node):

        svg = deepcopy(self.svg)
        svg.attrib["width"] = "100%"
        svg.attrib["height"] = ""
        

        base_path = self.options.dir
        xlink = "{http://www.w3.org/1999/xlink}"
        inkscape = "{http://www.inkscape.org/namespaces/inkscape}"

        for layer in svg.xpath(".//svg:g", namespaces=inkex.NSS):
            layer.attrib["style"] = layer.attrib.get("style", "").replace("display:none", "")
        
        for pth in svg.xpath(".//svg:path", namespaces=inkex.NSS):
            pth.attrib["style"] = pth.attrib.get("style", "").replace("context-stroke;", "black;")

        if not base_path in (None, ""):
            os.makedirs(os.path.join(base_path, reveal_js_path, "images"), exist_ok=True)
            for img in svg.xpath(".//svg:image", namespaces=inkex.NSS):
                href = img.attrib.get("%shref" % xlink, "")
                href = href.replace("file://", "")
                fn = os.path.basename(href)
                new_fn = os.path.join(base_path, reveal_js_path, "images", fn)
                if os.path.abspath(href) != os.path.abspath(new_fn):
                    shutil.copyfile(href, new_fn)
                
                img.attrib["src"] = os.path.join(reveal_js_path, "images", fn)
                

        for layer in svg.xpath("./svg:g/svg:g", namespaces=inkex.NSS):
            name = layer.attrib.get("%slabel" % inkscape, "")
            extra_class = re.findall(r'\[(.*?)\]', name)

            if len(extra_class) > 0:
                layer.attrib["class"] = "fragment" + " " + str(extra_class[0])
            else:
                layer.attrib["class"] = "fragment"

        top_level_layers = svg.xpath("./svg:g", namespaces=inkex.NSS)

        for top_level_layer in top_level_layers:
            for others in top_level_layers:
                others.attrib["display"] = "none"

            top_level_layer.attrib["display"] = "inline"

            slide = etree.Element("section")
            new_svg = deepcopy(svg)

            for element in new_svg.xpath("./svg:g", namespaces=inkex.NSS):
                if not element.attrib["id"] == top_level_layer.attrib["id"]:
                    new_svg.remove(element)

            slide.append(new_svg)
            slides_node.append(slide)

        #self.debug("Top level layers: " + str(len(top_level_layers)))



    def save(self, stream):
        html_parser = etree.HTMLParser()

        # unzip reveal js: 
        if self.options.install_revealjs:
            with zipfile.ZipFile(self.get_resource("reveal.js-master.zip")) as zip:
                zip.extractall(self.options.dir)

        if self.options.template and len(self.options.template) > 0:
            with open(self.options.template) as st:
                html = etree.parse(st, html_parser)
        else:
            with open(self.get_resource("slides_template.html")) as st:
                html = etree.parse(st, html_parser)

        slides_node = html.xpath("//div[@id='inkscape-slides']")

        if len(slides_node) == 0:
            raise inkex.AbortExtension("No element with id #inkscape-slides found in template file.")

        slides_node = slides_node[0]
        self.generate_slides(slides_node)
    
        html.write(stream, pretty_print=True, method='html')


if __name__ == "__main__":
    RevealExporter().run()