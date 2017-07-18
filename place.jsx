﻿#include "json2.js"#include "underscore.js"var files = Folder("/opt/westbook/data").getFiles();var DAY_OF_WEEK = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];var MONTH_OF_YEAR = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];_.each(files, function(file) {  file.open('r');  var content = file.read();  var data = JSON.parse(content);  var stories = data.stories;  var name = data.fullname  file.close();  stories = _.sortBy(stories, function(s) { return (s && s.story && -1 * s.story.length) || 0 });  var document = app.open("/opt/westbook/westbook-template.indd");  var masterFrames = document.textFrames;  for (var i=0; i < masterFrames.length; i++) {      if(masterFrames[i].name === "namedate") {          var date = new Date();          masterFrames[i].contents = name + "\r" + DAY_OF_WEEK[date.getDay()] + " " + MONTH_OF_YEAR[date.getMonth()] + " " + date.getDate() + ", " + date.getFullYear();      }  }  var frames= document.textFrames;  for (var i=0; i < frames.length; i++) {     fillFrame(frames[i], stories);  }  exportPDF(document, file);});function exportPDF(document, sourcefile) {  document.exportFile(ExportFormat.pdfType, File("/opt/westbook/pdf/" + (new Date()).getDate() + "/" + sourcefile.name + ".pdf"),false);}function getRequirements(group) {    var requirements = group.name.split("::")[1];    if (!requirements || "-1" == group.name.indexOf('story')) {        return false;    }    return requirements.split(",");}function validProps(story) {    return _.filter(_.keys(story), function(i) {        return story[i] && story[i].length && i !== "id";    });}function findStory(requirements, stories) {    var story = null;    var id = 0;    var cur;    var ok;    var props;    var clean;    var union;    while (!story && id < stories.length) {        cur = stories[id];        props = validProps(cur);        union = _.union(props, requirements);        ok = true;        // ensure stories and images go where they are visible        if (_.contains(union, "story")) {            ok = ok && _.contains(requirements, "story") && _.contains(props, "story");        }        if (_.contains(union, "image") && !_.contains(union, "story")) {            ok = ok && _.contains(requirements, "image") && _.contains(props, "image");        }        if (ok && !cur.used) {            story = cur;            story.used = true;        }        id++;    }    return story;}function addImage(story, frame) {    var graf = frame.parentStory.paragraphs.lastItem()    var insertPoint = graf.insertionPoints.lastItem();    insertPoint.contents = "\r";    var inlineFrame = insertPoint.textFrames.add();    var inlineBounds = inlineFrame.geometricBounds;    var width = frame.geometricBounds[3] - frame.geometricBounds[1];    if(story.story && story.story.length) {      inlineFrame.geometricBounds = [inlineBounds[0], inlineBounds[1], inlineBounds[0] + width/2, inlineBounds[1] + width];    } else {      inlineFrame.geometricBounds = [inlineBounds[0], inlineBounds[1], frame.geometricBounds[2], inlineBounds[1] + width];    }    with(inlineFrame.anchoredObjectSettings){        anchoredPosition = AnchorPosition.anchored;        anchorPoint = AnchorPoint.topLeftAnchor;        anchorYoffset = -.5;   }    inlineFrame.textWrapPreferences.textWrapMode = TextWrapModes.BOUNDING_BOX_TEXT_WRAP;    inlineFrame.place(story.image);    inlineFrame.pageItems.everyItem().fit(FitOptions.fillProportionally);}function addStory(story, frame) {    var graf = frame.parentStory.paragraphs.lastItem()    var insertPoint = graf.insertionPoints.lastItem();    insertPoint.contents = "\r";    var inlineFrame = insertPoint.textFrames.add();    frame.texts.item(0).recompose;    var inlineBounds = inlineFrame.geometricBounds;    var width = frame.geometricBounds[3] - frame.geometricBounds[1];    var height = inlineFrame.geometricBounds[0] - frame.geometricBounds[2];    inlineFrame.geometricBounds = [inlineBounds[0], inlineBounds[1], inlineBounds[0] + height, inlineBounds[1] + width];    with(inlineFrame.anchoredObjectSettings){        anchoredPosition = AnchorPosition.anchored;        anchorPoint = AnchorPoint.topLeftAnchor;   }    inlineFrame.contents = story.story;    var columnWidth = document.documentPreferences.pageWidth / 5;    var columnCount = Math.round(width / columnWidth);    inlineFrame.textFramePreferences.textColumnCount = Math.round(width / columnWidth);    inlineFrame.paragraphs.everyItem().applyParagraphStyle(document.paragraphStyles.item("story"));    inlineFrame.paragraphs.firstItem().applyParagraphStyle(document.paragraphStyles.item("storyfirst"));    if (columnCount < 3) {        inlineFrame.paragraphs.firstItem().applyParagraphStyle(document.paragraphStyles.item("storyfirst"));    } else {        inlineFrame.paragraphs.firstItem().applyParagraphStyle(document.paragraphStyles.item("storydrop"));    }    // Add Link    var linkFrame = inlineFrame.paragraphs.firstItem().insertionPoints.firstItem().textFrames.add();    linkFrame.geometricBounds = [frame.geometricBounds[2] - 1.9, frame.geometricBounds[3] - columnWidth + 1, frame.geometricBounds[2] , frame.geometricBounds[3]];    linkFrame.contents = story.link;    with(linkFrame.anchoredObjectSettings) {        anchoredPosition = AnchorPosition.anchored;        horizontalReferencePoint = AnchoredRelativeTo.textFrame;        verticalReferencePoint = AnchoredRelativeTo.textFrame;        anchorPoint = AnchorPoint.bottomRightAnchor;        anchorYoffset = -1 * height - .2;        anchorXoffset = -1 * width - 1;    }    linkFrame.textWrapPreferences.textWrapMode = TextWrapModes.BOUNDING_BOX_TEXT_WRAP;    linkFrame.paragraphs.everyItem().applyParagraphStyle(document.paragraphStyles.item("link"));}function fillFrame(frame, stories) {    var reqs = getRequirements(frame);    if (!reqs) {        return false;    }    var story = findStory(reqs, stories);    if (!story) {        return false;    }    var storyProps = validProps(story);    var props = _.intersection(storyProps, reqs);    var i, cur, style;    frame.parentStory.contents = "";    var usedStyles = [];    if (_.contains(props, "source")) {        usedStyles.push("source");        frame.parentStory.contents += story.source + "\r";    }    if (_.contains(props, "headline")) {      usedStyles.push("headline");      frame.parentStory.contents += story.headline + "\r";    }    if (_.contains(props, "deck")) {      if(_.contains(props, "headline") || story.deck.length > 100) {        usedStyles.push("deck");      } else {        usedStyles.push("headline");      }      frame.parentStory.contents += story.deck + "\r";    }    var i;    for (i=0; i < usedStyles.length; i++) {        frame.parentStory.paragraphs.item(i).applyParagraphStyle(document.paragraphStyles.item(usedStyles[i]));    }    if (_.contains(props, "image")) {      try { addImage(story, frame); } catch(e) {}    }    if (_.contains(props, "story")) {      try { addStory(story, frame); } catch (e) {}    }}