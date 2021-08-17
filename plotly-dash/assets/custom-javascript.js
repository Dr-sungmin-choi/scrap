let latitudeValue = 33.450701;
let longitudeValue = 126.570667;
let map;
let infoValues = [];
let imageSrc = "https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/markerStar.png"; 
let imageSize = new kakao.maps.Size(24, 35); 
let markerImage = new kakao.maps.MarkerImage(imageSrc, imageSize); 
let overlayArray = [];

function handleMapContainer(mapContainer) {
    mapOption = { 
        center: new kakao.maps.LatLng(latitudeValue, longitudeValue), // 지도의 중심좌표
        level: 2 // 지도의 확대 레벨
    };
    map = new kakao.maps.Map(mapContainer, mapOption); 
}

function waitMapAvailable() {
    let mapContainer = document.getElementById('page2-map')
    if (!mapContainer) {
        window.setTimeout(waitMapAvailable, 500);
        return;
    }
    return handleMapContainer(mapContainer);
}
waitMapAvailable();

function setCenter(map, latitude, longitude) {
    let moveLatLon = new kakao.maps.LatLng(latitude, longitude);  
    map.setCenter(moveLatLon)    
}

function displayMarker(map, data) { 
    let marker = new kakao.maps.Marker({
        map: map,
        position: data.latlng,
        title : data.title,
        image : markerImage
    });
    var overlay = new kakao.maps.CustomOverlay({
        position: marker.getPosition()
    });
    
    var content = document.createElement('div');
    content.classList.add('wrap')
    var infoDiv = document.createElement('div')
    infoDiv.classList.add('info')
    var titleDiv = document.createElement('div')
    titleDiv.classList.add('title')
    titleDiv.innerText = data.title
    infoDiv.appendChild(titleDiv)
    var bodyDiv = document.createElement('div')
    bodyDiv.classList.add('body')
    var descDiv = document.createElement('div')
    descDiv.classList.add('desc')
    var adDiv = document.createElement('div')
    adDiv.classList.add('ellipsis')
    adDiv.innerText = data.adroad
    var categoryDiv = document.createElement('div')
    categoryDiv.classList.add('ellipsis')
    categoryDiv.innerText = data.bigcategory + ' > ' + data.category
    descDiv.appendChild(categoryDiv)
    descDiv.appendChild(adDiv)
    bodyDiv.appendChild(descDiv)
    infoDiv.appendChild(bodyDiv)
    content.appendChild(infoDiv)
    overlay.setContent(content);
    overlayArray.push(overlay)
    kakao.maps.event.addListener(marker, 'mouseover', function() {
        overlay.setMap(map);
    });
    kakao.maps.event.addListener(marker, 'mouseout', function() {
        overlay.setMap(null);
    })
}

function median(data) {
    data = data.sort((a, b) => a - b)
    n = Math.floor(data.length / 2)
    return (data[n] + data[data.length - 1 - n]) / 2 }

let infoObserver = new MutationObserver((mutations, me) => {
    mutations.forEach((mutation) =>  {
        if (infoValues.length != mutation.target.childNodes.length) {
            infoValues = mutation.target.childNodes;
            let positions = [];
            let latArray = [];
            let lonArray = [];
            overlayArray = [];
            for (let i=0;i<infoValues.length;i++) {
                let t = infoValues[i].childNodes[0].innerText
                let lat = parseFloat(infoValues[i].childNodes[1].innerText)
                let lon = parseFloat(infoValues[i].childNodes[2].innerText)
                let adroad = infoValues[i].childNodes[3].innerText
                let bigcategory = infoValues[i].childNodes[4].innerText
                let category = infoValues[i].childNodes[5].innerText
                latArray.push(lat);
                lonArray.push(lon);
                positions.push({
                    title: t,
                    latlng: new kakao.maps.LatLng(lat, lon),
                    adroad: adroad,
                    bigcategory: bigcategory,
                    category: category
                })
            }
            setCenter(map, median(latArray), median(lonArray)) 
            
            for (let i=0; i<positions.length; i++) {
                let data = positions[i]
                console.log(data)
                displayMarker(map, data)
            }
        }
    })
});

function waitInfoObserverAvailable() {
    let infoContainer = document.getElementById('page2-store-list')
    if(!infoContainer) {
        //The node we need does not exist yet.
        //Wait 500ms and try again
        window.setTimeout(waitInfoObserverAvailable,500);
        return;
    }
    let config = {
        characterData: true,
        attributes: true,
        childList: true,
        subtree: true
    };
    infoObserver.observe(infoContainer,config);
}
waitInfoObserverAvailable();
