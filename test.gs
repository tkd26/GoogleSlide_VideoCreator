function onInstall(event) {
  onOpen(event);
}

function onOpen(event) {
  var ui = SlidesApp.getUi();

  Logger.log(Session.getActiveUserLocale());

  ui.createMenu('追加メニュー')
    .addItem('保存', 'saveNoteAndImages')
    .addToUi();
}
  
function saveNoteAndImages() {
  var ui = SlidesApp.getUi();
  
  var result = ui.prompt(
    'スライドとノートを保存しますか?',
    'ファイル名を変えたい場合は入力してください．',
    ui.ButtonSet.OK_CANCEL);
  
  var presentation = SlidesApp.getActivePresentation();
  var presentationName = presentation.getName();
  
  var button = result.getSelectedButton();
  var text = result.getResponseText();
  if (button == ui.Button.OK) {
    saveScenarioSlideImages(text ? text : presentationName);
  } else if (button == ui.Button.CANCEL) {
  } else if (button == ui.Button.CLOSE) {
  }
}
  
function downloadSlide(folder, name, presentationId, slideId) {
  var url = 'https://docs.google.com/presentation/d/' + presentationId + '/export/jpeg?id=' + presentationId + '&pageid=' + slideId;
  var options = {
    headers: {
      Authorization: 'Bearer ' + ScriptApp.getOAuthToken()
    }
  };
  var response = UrlFetchApp.fetch(url, options);
  var image = response.getAs(MimeType.JPEG);
  image.setName(name);
  folder.createFile(image);
}
  
function saveScenarioSlideImages(presentationName) {
  var presentation = SlidesApp.getActivePresentation();
  var scenario = [];
  var folder = DriveApp.createFolder(presentationName);
  presentation.getSlides().forEach(function(slide, i) {
    var pageName = Utilities.formatString('%03d', i+1)+'.jpeg';

    var txt = '';
    slide.getNotesPage().getShapes().forEach(function(shape, i) {
      txt += shape.getText().asString();
    });
  
    var note = [];
    txt.split('\n').map( function(t) { return t.trim() } ).forEach( function(v) {
      if (v == '') {
        //note.push(v);
      } else {
        note.push(v);
      }
    });
  
    scenario = scenario.concat(note);
    scenario.push(':newpage');
    downloadSlide(folder, pageName, presentation.getId(), slide.getObjectId());

  });
  folder.createFile('text.txt',scenario.join('\n'));
}
  
  
  