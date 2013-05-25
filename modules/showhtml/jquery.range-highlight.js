/*
 * jQuery range highlight plugin
 *
 * Thanks to Johann Burkard and Bartek Szopka; I borrowed some of their code to make this.
 *
 */

jQuery.extend({
    highlight: function (node, start, len) {
        // console.log('1', node.nodeType)
        if (node.nodeType === 3) {
            // console.log('2')
            if (node.data.length <= start) return start - node.data.length;
            var highlight = document.createElement('span');
            highlight.className = 'highlight';
            // console.log(node);
            var hlNode = node.splitText(start);
            hlNode.splitText(len);
            var hlClone = hlNode.cloneNode(true);
            highlight.appendChild(hlClone);
            hlNode.parentNode.replaceChild(highlight, hlNode);
            return -1;
        } else if ((node.nodeType === 1 && node.childNodes) && // only element nodes that have children
                !/(script|style)/i.test(node.tagName) && // ignore script and style nodes
                !(node.tagName === 'SPAN' && node.className === 'highlight')) { // skip if already highlighted
            // console.log('3')
            var s = start;
            for (var i = 0; i < node.childNodes.length; i++) {
                // console.log('4')
                s = jQuery.highlight(node.childNodes[i], s, len);
                if (s === -1) break;
            }
        }
        return start;
    }
});

jQuery.fn.unhighlight = function (options) {
    var settings = { className: 'highlight', element: 'span' };
    jQuery.extend(settings, options);

    return this.find(settings.element + "." + settings.className).each(function () {
        var parent = this.parentNode;
        parent.replaceChild(this.firstChild, this);
        parent.normalize();
    }).end();
};

jQuery.fn.highlight = function (start, end) {
    return this.each(function () {
        jQuery.highlight(this, start, end - start);
    });
};

