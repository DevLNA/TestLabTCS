let base
let eixo
let tubo

let inconsolata
let data = {}
let date, hour, ah, dec, cup, tube
let color_slider
let multi_slider_size = 150


async function getJSONData() {
  try {
    const response = await fetch('http://localhost:5050/api/telescope/position');
    
    data = await response.json();
    
  } catch (error) {
    console.error('Error:', error);
  }
}

function preload() {
  base = loadModel("static/assets/Pilar_PE160.obj", false)
  eixo = loadModel("static/assets/Eixo_PE160.obj", false)
  tubo = loadModel("static/assets/Tubo_PE160.obj", false)
  inconsolata = loadFont('static/assets/Inconsolata.otf')
  // data = loadJSON('static/assets/data.json')
  setInterval(getJSONData, 150)
}


function setup() {
  createCanvas(windowWidth, windowHeight, WEBGL)
  textFont(inconsolata)
  textSize(height / 45)
  textAlign(CENTER, CENTER)

}
let value = -180;

function mouseDragged() {
  value = mouseX;

}

function draw() {
  background(130)
  box(1);

  if (data.hourAngle) {  // Atualiza o valor apenas se ele realmente existir. Ação para que não apareça 'UNDEFINED' como resultado
    ah = data.hourAngle
    dec = data.declination
    if (ah > 0) {
      ah = ah - 12
      dec = 180 - dec
    } 
  } else {
    ah = 0
    dec = -22.5
  }

  // fill(150, 0, 100)
  noFill()

  scale(.18)
  // normalMaterial()
  fill(152, 13, 59) // Atribui cor ao modelo
  

  rotateY(value * PI / 180)

  rotateX(-202.25 * PI / 180) // É nessa linha que sera somado 22.5 graus
  strokeWeight(.1)
  model(base)
  rotateZ(-ah*15 * PI / 180) // Aqui configura o valor do Eixo RA (+/-4,5 ah)

  translate(0, 0, 0) //Offset para coincidir os pivôs da base e do eixo

  strokeWeight(.1)
  model(eixo)
  translate(260, 0, 0) //Offset para coincidir os pivôs do eixo e do tubo
  rotateX(-22.25 * PI / 180)  // Aqui configura a Latitude
  rotateX(-1 * (dec) * PI / 180)  // Aqui configura o valor do eixo DEC (+57 N e -80 S)
  fill(246, 245, 240)
  strokeWeight(.5)
  model(tubo)
  
  


}