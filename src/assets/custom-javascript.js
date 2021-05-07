let latitudeValue = 33.450701;
let longitudeValue = 126.570667;
let map;
let infoValues = []

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

function waitCenterChangeAvailable(latitude, longitude) {
    if (map == undefined) {
        window.setTimeout(waitMapChangeAvailable, 500);
        return;
    }
    return setCenter(map, latitude, longitude)
}

let centerObserver = new MutationObserver((mutations, me) => {
    mutations.forEach((mutation) =>  {
        if (longitudeValue != mutation.target.innerText & mutation.target.innerText != undefined) {
            longitudeValue = mutation.target.innerText;
            latitudeValue = document.getElementById('page2-latitude').innerText;
            waitCenterChangeAvailable(parseFloat(latitudeValue), parseFloat(longitudeValue));
            // console.log(longitudeValue)
            // console.log(latitudeValue)
        }
    })
});

function waitCenterObserverAvailable() {
    let longitudeContainer = document.getElementById('page2-longitude')
    if(!longitudeContainer) {
        //The node we need does not exist yet.
        //Wait 500ms and try again
        window.setTimeout(waitCenterObserverAvailable,500);
        return;
    }
    let config = {
        characterData: true,
        attributes: true,
        childList: false,
        subtree: true
    };
    centerObserver.observe(longitudeContainer,config);
}
waitCenterObserverAvailable();

let infoObserver = new MutationObserver((mutations, me) => {
    mutations.forEach((mutation) =>  {
        if (infoValues.length != mutation.target.childNodes.length) {
            infoValues = mutation.target.childNodes;
            let positions = [];

            for (let i=0;i<infoValues.length;i++) {
                let t = infoValues[i].childNodes[0].innerText
                let lat = parseFloat(infoValues[i].childNodes[1].innerText)
                let lon = parseFloat(infoValues[i].childNodes[2].innerText)
                positions.push({ title: t, latlng: new kakao.maps.LatLng(lat, lon) })
            }  
            
            let imageSrc = "https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/markerStar.png"; 
    
            for (let i=0; i<positions.length; i++) {
                
                // 마커 이미지의 이미지 크기 입니다
                let imageSize = new kakao.maps.Size(24, 35); 
                
                // 마커 이미지를 생성합니다    
                let markerImage = new kakao.maps.MarkerImage(imageSrc, imageSize); 
                
                // 마커를 생성합니다
                let marker = new kakao.maps.Marker({
                    map: map, // 마커를 표시할 지도
                    position: positions[i].latlng, // 마커를 표시할 위치
                    title : positions[i].title, // 마커의 타이틀, 마커에 마우스를 올리면 타이틀이 표시됩니다
                    image : markerImage // 마커 이미지 
                });
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
