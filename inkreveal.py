import os 
import zipfile
import shutil
import re

from copy import deepcopy
import urllib

from lxml import etree


reveal_js_path = "reveal.js-master"
images_path = "images"

import inkex 

class RevealExporter(inkex.OutputExtension):
    def add_arguments(self, parser):
        parser.add_argument("--tab")
        parser.add_argument("--template")
        parser.add_argument("--install_revealjs")

    def validate_inputs(self):
        pass

    def generate_slides(self, slides_node):

        svg = deepcopy(self.svg)
        svg.attrib["width"] = "100%"
        svg.attrib["height"] = ""
        


        xlink = "{http://www.w3.org/1999/xlink}"
        inkscape = "{http://www.inkscape.org/namespaces/inkscape}"

        for layer in svg.xpath(".//svg:g", namespaces=inkex.NSS):
            layer.attrib["style"] = layer.attrib.get("style", "").replace("display:none", "")
        
        for pth in svg.xpath(".//svg:path", namespaces=inkex.NSS):
            pth.attrib["style"] = pth.attrib.get("style", "").replace("context-stroke;", "black;")

        if not self.base_path in (None, ""):
            os.makedirs(os.path.join(self.base_path, images_path), exist_ok=True)

            for img in svg.xpath(".//svg:image", namespaces=inkex.NSS):
                href = urllib.parse.unquote(img.attrib.get("%shref" % xlink, ""))

                if href.startswith("data:"):
                    continue

                href = href.replace("file://", "")
                href = self.absolute_href(href)

                fn = os.path.basename(href)
                new_fn = os.path.join(self.base_path, images_path, fn)
                if os.path.abspath(href) != os.path.abspath(new_fn):
                    shutil.copy(href, new_fn)
                
                img.attrib["src"] = os.path.join(images_path, fn)
                img.attrib["%shref" % xlink] = os.path.join(images_path, fn)


        for layer in svg.xpath("./svg:g/svg:g", namespaces=inkex.NSS):
            name = layer.attrib.get("%slabel" % inkscape, "")
            extra_class = re.findall(r'\[(.*?)\]', name)

            if len(extra_class) > 0:
                layer.attrib["class"] = "fragment" + " " + str(extra_class[0])
            else:
                layer.attrib["class"] = "fragment"

        for rect in svg.xpath(".//svg:rect", namespaces=inkex.NSS):
            
            # if the rect element has a desc as a child, replace the rect element 
            # with a foreignObject element which constrains the text of the desc as the innerHtml
            # of the foreignObject element
            if len(rect.xpath("./svg:desc", namespaces=inkex.NSS)) > 0:
                # get the desc element
                desc = rect.xpath("./svg:desc", namespaces=inkex.NSS)[0]

                # create a new foreignObject element
                foreignObject = etree.Element("foreignObject")


                # set the x, y, width and height attributes of the foreignObject element
                foreignObject.attrib["x"] = rect.attrib["x"]
                foreignObject.attrib["y"] = rect.attrib["y"]
                foreignObject.attrib["width"] = rect.attrib["width"]
                foreignObject.attrib["height"] = rect.attrib["height"]

                innerHTML = desc.text
                variables = {'w': float(rect.attrib["width"]), 'h': float(rect.attrib["height"])}
                variables["content_width"] = "1024"

                # find all regular expressions of the from X = "Y" where X is a variable name and Y is a value
                # store all variables in a dictionary. Allow spaces before or after the = sign.
                variables.update(dict(re.findall(r'(\w+)\s*=\s*"([^"]+)"', innerHTML)))

                variables["zoom"] = float(variables.get("zoom", variables["w"] / float(variables["content_width"])))

                foreignObject.attrib["width"] = str(variables["w"] / variables["zoom"])
                foreignObject.attrib["height"] = str(variables["h"] / variables["zoom"])
                foreignObject.attrib["style"] = f"""transform: scale({variables["zoom"]}); transform-origin: top left;"""
                foreignObject.attrib["x"] = str(float(rect.attrib["x"]) / variables["zoom"])
                foreignObject.attrib["y"] = str(float(rect.attrib["y"]) / variables["zoom"])


                if "{{video" in innerHTML:
                    innerHTML = f"""
                    <video width="{variables['w'] / variables['zoom']}" height="{variables['h'] / variables['zoom']}" data-autoplay="true" autoplay="true" loop="true" data-loop="true">
                        <source src="{variables['src']}" type="video/mp4"></source>
                        Your browser does not support the video tag.
                    </video>
                    """

                elif "{{iframe" in innerHTML:
                    innerHTML = f"""
                    <iframe width="{variables['w'] / variables["zoom"] }" height="{variables['h'] / variables["zoom"] }" src="{variables['src']}" scrolling="no">
                    </iframe>
                    """
                elif "{{youtube" in innerHTML:
                    innerHTML = f"""
                    <iframe width="{variables['w'] / variables["zoom"] }" height="{variables['h'] / variables["zoom"] }" 
                    src="https://www.youtube.com/embed/{variables['src']}" 
                    title="YouTube video player" frameborder="0" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen="true" data-preload="true">
                    </iframe>
                    """
                else:
                    innerHTML = innerHTML.format(**variables)
                
                # parse innerHTML as html and append it to the foreignObject element
                foreignObject.append(etree.fromstring("<body xmlns='http://www.w3.org/1999/xhtml'>" + 
                                                    innerHTML +
                                                    "</body>"))
                    
 
                # replace the rect element with the foreignObject element
                rect.getparent().replace(rect, foreignObject)

                # remove the desc element
                rect.remove(desc)


        top_level_layers = svg.xpath("./svg:g", namespaces=inkex.NSS)

        for top_level_layer in top_level_layers:
            for others in top_level_layers:
                others.attrib["display"] = "none"

            top_level_layer.attrib["display"] = "inline"

            if len(top_level_layer.xpath("./svg:desc", namespaces=inkex.NSS)) > 0:
                # get the desc element
                desc = top_level_layer.xpath("./svg:desc", namespaces=inkex.NSS)[0]

                # create a new foreignObject element
                slide = etree.fromstring("<section " + desc.text + "></section>")
            else:
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

        self.base_path = self.svg_path()

        # unzip reveal js: 
        if self.options.install_revealjs:
            with zipfile.ZipFile(self.get_resource("reveal.js-master.zip")) as zip:
                zip.extractall(self.base_path)

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