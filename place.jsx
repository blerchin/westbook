﻿#include "json2.js"#include "underscore.js"var storyFile = File("/opt/westbook/ben_lerchin.com.json");var stories = null;var content;storyFile.open('r');content = storyFile.read();stories = JSON.parse(content);storyFile.close();stories = _.sortBy(stories, function(s) { return (s.story && -1 * s.story.length) || 0 });var styles = [    "source",    "headline",    "deck",    "story",    "link"];var document = app.open("/opt/westbook/westbook-template.indd");var frames= document.textFrames;for (var i=0; i < frames.length; i++) {   fillFrame(frames[i]); }function getRequirements(group) {    var requirements = group.name.split("::")[1];    if (!requirements || "-1" == group.name.indexOf('story')) {        return false;    }    return requirements.split(",");}function findStory(requirements) {    var story = null;    var id = 0;    var cur;    var ok;    var req;    var props;    var clean;    while (!story && id < stories.length) {        cur = stories[id];        props = _.filter(_.keys(cur), function(i) {            return cur[i] && cur[i].length && i !== "id";        });                ok = !_.difference(props, requirements).length && !_.difference(requirements, props).length ;        if (ok && !cur.used) {            story = cur;            story.used = true;        }        id++;    }    return story;}function fillFrame(frame) {    var reqs = getRequirements(frame);    if (!reqs) {        return false;    }    var story = findStory(reqs);    if (!story) {        return false;    }    var i, cur, style;    frame.parentStory.contents = "";    var usedStyles = [];    if (_.contains(reqs, "source")) {        usedStyles.push("source");        frame.parentStory.contents += story.source + "\r";    }    if (_.contains(reqs, "headline")) {        usedStyles.push("headline");        frame.parentStory.contents += story.headline + "\r";    }   if (_.contains(reqs, "deck")) {        usedStyles.push("deck");        frame.parentStory.contents += story.headline + "\r";    }    if (_.contains(reqs, "story")) {//        usedStyles += "storyfirst";        usedStyles.push("story");        frame.parentStory.contents += story.story + "\r";    }    if (_.contains(reqs, "link")) {        usedStyles.push("link");        frame.parentStory.contents += story.link;    }    frame.parentStory.paragraphs.itemByRange(0, frame.parentStory.paragraphs.length - 1).applyParagraphStyle(document.paragraphStyles.item("story"));    var i;    for (i=0; i < usedStyles.length - 1; i++) {        $.writeln(i);        frame.parentStory.paragraphs.item(i).applyParagraphStyle(document.paragraphStyles.item(usedStyles[i]));    }    if (_.contains(usedStyles, "link")) {        frame.parentStory.paragraphs.lastItem().applyParagraphStyle(document.paragraphStyles.item("link"));    }    if (_.contains(reqs, "image")) {        var graf = frame.parentStory.paragraphs.item(_.indexOf(usedStyles, "deck") + 1)        graf.applyParagraphStyle(document.paragraphStyles.item("storyfirst"));        var insertPoint = graf.insertionPoints.item(0);        insertPoint.contents = "\n";        var inlineFrame = insertPoint.textFrames.add();        var inlineBounds = inlineFrame.geometricBounds;        var frameBounds = frame.geometricBounds;        var width = frameBounds[3] - frameBounds[1];        var bounds = [inlineBounds[0], inlineBounds[1], inlineBounds[0] + width/2, inlineBounds[1] + width];        inlineFrame.geometricBounds = bounds;        with(inlineFrame.anchoredObjectSettings){            anchoredPosition = AnchorPosition.anchored;            anchorPoint = AnchorPoint.topLeftAnchor;            anchorYoffset = -.5;       }        inlineFrame.textWrapPreferences.textWrapMode = TextWrapModes.BOUNDING_BOX_TEXT_WRAP;        inlineFrame.place(story.image);    }}