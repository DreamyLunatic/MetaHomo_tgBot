// https://leafletjs.com/reference.html
// https://tomickigrzegorz.github.io/leaflet-examples/
// https://github.com/slutske22/leaflet-popup-modifier
// https://codesandbox.io/s/leaflet-popup-modifier-kbuwd


let tg = window.Telegram.WebApp;
tg.expand(); //разворачиваем на все окно

const searchParams = new URLSearchParams(window.location.search);

const expire = new Date();
expire.setHours(expire.getHours() + (24 * 10));

// получаем токены переданные при "/start" из telegram
if (searchParams.has('refresh')) {
    setCookie('refreshToken', searchParams.get('refresh'), options = {expires: expire});
};

if (searchParams.has('access')) {
    setCookie('accessToken', searchParams.get('access'), options = {expires: expire});
};

// создаём новый pathname с префиксом языка
let newLocationPathname = '/'

if (window.location.pathname.startsWith('/en')){
    newLocationPathname = '/en/';
} else if (window.location.pathname.startsWith('/ru')){
    newLocationPathname = '/ru/';
} else if (window.location.pathname.startsWith('/uk')){
    newLocationPathname = '/uk/';
}
// console.log('***** newLocationPathname: ' + newLocationPathname);
// очищаем url от токенов переданных при "/start" из telegram
window.history.replaceState({}, 'Main page', newLocationPathname);

// magnification with which the map will start
let zoom = 8;
let lat = 48.56706;
let lng = 2.36206;

if (mapLatitudeCenter && mapLongitudeCenter) {
    lat = mapLatitudeCenter;
    lng = mapLongitudeCenter;
}

if (mapZoom) {
    zoom = mapZoom;
}

let map = L.map('map').setView([lat, lng], zoom);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap'
}).addTo(map);

function markerPopupOptions(isOwner, markerId, markerTime, markerTelegramUsername, markerMessage, markerPhoto) {
    return {
        removable: isOwner,
        editable: isOwner,
        savable: isOwner,
        maxWidth: 300,
        autoPan: true,
        markerId: markerId,
        markerTime: markerTime,
        markerTelegramUsername: markerTelegramUsername,
        markerMessage: markerMessage,
        markerPhoto: markerPhoto,
    };
}

function markerPopupData(time, id, telegramUsername, latitude, longitude, message, photo) {
    let photoElement = photo ? `<img class="image-popup" src="${photo}" width=200px>` : '';

    return `
        <b>${time}</b><br>
        <i>marker id: <span class="marker_id">${id}</span>, user: <span class="user">${telegramUsername}</span></i><br>
        <span>latitude: ${latitude}, longitude: ${longitude}</span><br>
        <span><b>${message}</b></span>
        <div name='imageEl'>${photoElement}</div>
    `;
}

////////////////////////////////////////////////////

const markerPlace = document.querySelector(".marker-position");
let latCenter;
let lngCenter;
// on drag end
map.on("dragend", setRentacle);
// second option, by dragging the map
map.on("dragstart", updateInfo);
// on zoom end
map.on("zoomend", setRentacle);
// update info about bounds when site loaded
document.addEventListener("DOMContentLoaded", function () {
    const bounds = map.getBounds();
    latCenter = (bounds._northEast.lat - (bounds._northEast.lat - bounds._southWest.lat) / 2).toFixed(5);
    lngCenter = (bounds._northEast.lng - (bounds._northEast.lng - bounds._southWest.lng) / 2).toFixed(5);
    updateInfo(bounds._northEast, bounds._southWest, latCenter, lngCenter);
});
// set rentacle function
function setRentacle() {
    const bounds = map.getBounds();
    latCenter = (bounds._northEast.lat - (bounds._northEast.lat - bounds._southWest.lat) / 2).toFixed(5);
    lngCenter = (bounds._northEast.lng - (bounds._northEast.lng - bounds._southWest.lng) / 2).toFixed(5);
    updateInfo(bounds._northEast, bounds._southWest, latCenter, lngCenter);
}
// update info about bounds
function updateInfo(north, south, latCenter, lngCenter) {
    markerPlace.textContent =
      south === undefined
        ? "We are moving the map..."
        : `Map Center: LatLng(${latCenter}, ${lngCenter})`;
        // : `SouthWest: ${south}, NorthEast: ${north}, Map Center: LatLng(${latCenter}, ${lngCenter})`;
}

///////////// Tokens /////////////////
console.log('refreshToken: ' + getCookie('refreshToken'));
console.log('accessToken: ' + getCookie('accessToken'));
//////////////////////////////////////////////////////
let addMarkerButton = document.getElementById('addMarkerButton');
addMarkerButton.addEventListener('click', addMarker);

var addMarkerIcon = L.icon({
    iconUrl:"/static/styles/leaflet_1.6.0/images/marker-icon-purple.png",
    iconRetinaUrl:"/static/styles/leaflet_1.6.0/images/marker-icon-2x-purple.png",
    shadowUrl:"/static/styles/leaflet_1.6.0/images/marker-shadow.png",
    iconSize:[25,41],
    iconAnchor:[12,41],
    popupAnchor:[1,-34],
    tooltipAnchor:[16,-28],
    shadowSize:[41,41]
});

function addMarker(e) {
    let isOwner = true;
    let popupOptions = markerPopupOptions(isOwner, '', '', '', '', '');
    let popupData = markerPopupData('', '', '', latCenter, lngCenter, '', '');

    let marker = L.marker(
        [latCenter, lngCenter],
        {
            draggable: isOwner,
            icon: addMarkerIcon,
        }
    )
    .addTo(map)
    .bindPopup(
        popupData,
        popupOptions
    );

    marker.on("dragend", dragedMaker);
}

/////////////// draged /////////////
function dragedMaker() {
    this._popup._content = markerPopupData(
        this._popup.options.markerTime,
        this._popup.options.markerId,
        this._popup.options.markerTelegramUsername,
        (this.getLatLng().lat).toFixed(5),
        (this.getLatLng().lng).toFixed(5),
        this._popup.options.markerMessage,
        this._popup.options.markerPhoto
    );
}

/////////////////// Update Map ///////////////////////////////////
document.addEventListener("DOMContentLoaded", updateMap);

function updateMap() {

    fetchDataForGetListMarker('markers/')
        .then(data => {
            console.log('(fetchDataForGetListMarker) Полученные данные:', data);
            addMarkersToMap(data);
        })
        .catch(error => {
            console.error('Ошибка:', error);
        });

}

async function fetchDataForGetListMarker(url) {
    const newAccessToken = await refreshToken();

    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                // 'Content-Type': 'application/json',
                'Authorization': `Bearer ${getCookie('accessToken')}`
            },
        });
        const responseJson = await response.json();
        if (!response.ok) {
            if (responseJson.code === 'token_not_valid' && responseJson.messages.some(msg => msg.message === 'Token is invalid or expired')) {
                const newAccessToken = await refreshToken();
                return fetchDataForGetListMarker(url);
            } else {
                throw new Error(`HTTP error! Status: ${response.status}, Response: ${JSON.stringify(responseJson)}`);
            }
        }
        return responseJson;
    } catch (error) {
        console.error('Ошибка при выполнении запроса:', error);
        throw error;
    }
}

var currentUserIcon = L.icon({
    iconUrl:"/static/styles/leaflet_1.6.0/images/marker-icon-dark-blue.png",
    iconRetinaUrl:"/static/styles/leaflet_1.6.0/images/marker-icon-2x-dark-blue.png",
    shadowUrl:"/static/styles/leaflet_1.6.0/images/marker-shadow.png",
    iconSize:[25,41],
    iconAnchor:[12,41],
    popupAnchor:[1,-34],
    tooltipAnchor:[16,-28],
    shadowSize:[41,41]
});

function addMarkersToMap(markers){
    for (let i = 0; i < markers.length; i += 1) {

        let popupOptions = markerPopupOptions(
            markers[i]['is_owner'],
            markers[i]['id'],
            markers[i]['time'],
            markers[i]['telegram_username'],
            markers[i]['message'],
            markers[i]['photo']
        );

        let popupData = markerPopupData(
            markers[i]['time'],
            markers[i]['id'],
            markers[i]['telegram_username'],
            markers[i]['latitude'],
            markers[i]['longitude'],
            markers[i]['message'],
            markers[i]['photo']
        );

        let markerOptions = {
            markerId: markers[i]['id'],
            draggable: markers[i]['is_owner'],
        };

        if (markers[i]['is_owner']) {
            markerOptions['icon'] = currentUserIcon;
        };

        let marker = L.marker(
            [markers[i]['latitude'], markers[i]['longitude']],
            markerOptions
        )
        .addTo(map)
        .bindPopup(popupData, popupOptions);

        // let marker = L.marker(
        //     [markers[i]['latitude'], markers[i]['longitude']],
        //     {
        //         markerId: markers[i]['id'],
        //         draggable: markers[i]['is_owner'],
        //     }
        // )
        // .addTo(map)
        // .bindPopup(popupData, popupOptions);

        marker.on("dragend", dragedMaker);
    };
}

///////////// create new marker  ///////////////

async function refreshToken() {
    const refreshToken = getCookie('refreshToken');
    if (!refreshToken) {
        alert('Refresh token not found.\n Enter the command "/start" in the Telegram to update Refresh Token.');
        throw new Error('Refresh token not found');
    }

    const response = await fetch('/api/token/refresh/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ refresh: refreshToken })
    });

    if (!response.ok) {
        const responseJson = await response.json();
        if (responseJson) {
            if ('code' in responseJson && 'messages' in responseJson) {

                if (responseJson.code === 'token_not_valid' && responseJson.messages.some(msg => msg.message === 'Token is invalid or expired')) {
                    alert('Token is invalid or expired.\n Enter the command "/start" in the Telegram to update Refresh Token.');
                }

            } else if ("Token is blacklisted" in responseJson.non_field_errors) {
                alert('Token is blacklisted.\n Enter the command "/start" in the Telegram to update Refresh Token.');
            }

            throw new Error(`Unable to refresh token: ${JSON.stringify(responseJson)}`);
        } else {
            alert('Enter the command "/start" in the Telegram to update Refresh Token.');
        }
    }

    const data = await response.json();
    // setCookie('accessToken', data.access, { path: '/', secure: true, 'max-age': 3600 });
    setCookie('accessToken', data.access, {expires: expire});
    console.log('const newAccessToken: ');
    console.log(data.access);
    return data.access;
}

async function fetchDataForCreateMarker(url, formData) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getCookie('accessToken')}`
            },
            body: formData,
        });
        const responseJson = await response.json();
        if (!response.ok) {
            if (responseJson.code === 'token_not_valid' && responseJson.messages.some(msg => msg.message === 'Token is invalid or expired')) {
                const newAccessToken = await refreshToken();
                return fetchDataForCreateMarker(url, formData);
            } else {
                throw new Error(`HTTP error! Status: ${response.status}, Response: ${JSON.stringify(responseJson)}`);
            }
        }
        return responseJson;
    } catch (error) {
        console.error('Ошибка при выполнении запроса:', error);
        throw error;
    }
}

function createMarker(formData, this_marker) {
    fetchDataForCreateMarker('markers/create/', formData)
        .then(data => {
            console.log('(fetchDataForCreateMarker) Полученные данные:', data);
            if (data['marker_id'] && !this_marker.options.markerId) {
                this_marker.options.markerId = data['marker_id'];
            };
            addMarkersToMap(data);
            alert('Marker create successfully!');
        })
        .catch(error => {
            console.error('Ошибка:', error);
        });
}

///////////// update marker  ///////////////
async function fetchDataForUpdateMarker(url, formData) {
    try {
        const response = await fetch(url, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${getCookie('accessToken')}`
            },
            body: formData,
        });
        const responseJson = await response.json();
        if (!response.ok) {
            if (responseJson.code === 'token_not_valid' && responseJson.messages.some(msg => msg.message === 'Token is invalid or expired')) {
                const newAccessToken = await refreshToken();
                return fetchDataForUpdateMarker(url, formData);
            } else {
                throw new Error(`HTTP error! Status: ${response.status}, Response: ${JSON.stringify(responseJson)}`);
            }
        }
        return responseJson;
    } catch (error) {
        console.error('Ошибка при выполнении запроса:', error);
        throw error;
    }
}


function updateMarker(formData, markerId) {
    fetchDataForUpdateMarker(`markers/${markerId}/update/`, formData)
        .then(data => {
            console.log('(fetchDataForUpdateMarker) Полученные данные:', data);
            alert('Marker update successfully!');
        })
        .catch(error => {
            console.error('Ошибка:', error);
        });
}


//////////////// Delete marker //////////////////////
function deleteMarker(markerId) {
    fetchDataForDeleteMarker(`markers/${markerId}/delete/`)
        .then(data => {
            console.log('(fetchDataForDeleteMarker) Полученные данные:', data);
            alert('Marker deleted successfully!');
        })
        .catch(error => {
            console.error('Ошибка:', error);
        });
}

async function fetchDataForDeleteMarker(url) {
    try {
        const response = await fetch(url, {
            method: 'DELETE',
            headers: {
                // 'Content-Type': 'application/json',
                'Authorization': `Bearer ${getCookie('accessToken')}`
            },
        });
        console.log('delete response: ');
        console.log(response);
        console.dir(response);

        if (!response.ok) {
            const responseJson = await response.json();
            if (responseJson.code === 'token_not_valid' && responseJson.messages.some(msg => msg.message === 'Token is invalid or expired')) {
                const newAccessToken = await refreshToken();
                return fetchDataForDeleteMarker(url);
            } else {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
        }
        return response;
    } catch (error) {
        console.error('Ошибка при выполнении запроса:', error);
        throw error;
    }
}

//////////////////////
//  Adding new options to the default options of a popup
L.Popup.mergeOptions({
    removable: false,
    editable: false,
    sevable: false,
});

// Modifying the popup mechanics
L.Popup.include({

    // modifying the _initLayout method to include edit and remove buttons, if those options are enabled

    //  ----------------    Source code  start ---------------------------- //
    // original from https://github.com/Leaflet/Leaflet/blob/master/src/layer/Popup.js
    _initLayout: function () {
        let prefix = 'leaflet-popup', container = this._container = L.DomUtil.create(
            'div', prefix + ' ' + (this.options.className || '') + ' leaflet-zoom-animated'
        );

        let wrapper = this._wrapper = L.DomUtil.create('div', prefix + '-content-wrapper', container);
        this._contentNode = L.DomUtil.create('div', prefix + '-content', wrapper);

        L.DomEvent.disableClickPropagation(wrapper);
        L.DomEvent.disableScrollPropagation(this._contentNode);
        L.DomEvent.on(wrapper, 'contextmenu', L.DomEvent.stopPropagation);

        this._tipContainer = L.DomUtil.create('div', prefix + '-tip-container', container);
        this._tip = L.DomUtil.create('div', prefix + '-tip', this._tipContainer);

        if (this.options.closeButton) {
            let closeButton = this._closeButton = L.DomUtil.create('a', prefix + '-close-button', container);
            closeButton.href = '#close';
            closeButton.innerHTML = '&#215;';

            L.DomEvent.on(closeButton, 'click', this._onCloseButtonClick, this);
        }

        //  ----------------    Source code end ---------------------------- //

        if (this.options.editable && this.options.removable && this.options.savable){
            let userActionButtons = this._userActionButtons = L.DomUtil.create('div', prefix + '-useraction-buttons', wrapper);
            let removeButton = this._removeButton = L.DomUtil.create('a', prefix + '-remove-button', userActionButtons);
            removeButton.href = '#close';
            removeButton.innerHTML = 'Delete marker';
            let editButton = this._editButton = L.DomUtil.create('a', prefix + '-edit-button', userActionButtons);
            editButton.href = '#edit';
            editButton.innerHTML = 'Edit';
            let sendButton = this._sendButton = L.DomUtil.create('a', prefix + '-send-button', userActionButtons);
            sendButton.href = '#send';
            sendButton.innerHTML = 'Send data';
            this.options.minWidth = 300;

            L.DomEvent.on(removeButton, 'click', this._onRemoveButtonClick, this);
            L.DomEvent.on(editButton, 'click', this._onEditButtonClick, this);
            L.DomEvent.on(sendButton, 'click', this._onSendButtonClick, this);
        }
    },

    _onRemoveButtonClick: function (e) {
        this._source.remove();
        L.DomEvent.stop(e);

        let event = new CustomEvent("removeMarker", {
            detail: { marker: this._source}
        });

        document.dispatchEvent(event);

        if (this.options.markerId) {
            deleteMarker(this.options.markerId);
        };
    },

    _onEditButtonClick: function (e) {
        //Needs to be defined first to capture width before changes are applied
        let inputFieldWidth = this._inputFieldWidth = this._container.offsetWidth - 2*19;

        this._userActionButtons.style.display = "none";

        let wrapper = this._wrapper;
        let editScreen = this._editScreen = L.DomUtil.create('div', 'leaflet-popup-edit-screen', wrapper)
        let inputField = this._inputField = L.DomUtil.create('div', 'leaflet-popup-input', editScreen);
        inputField.setAttribute("contenteditable", "true");
        inputField.innerHTML = this.options.markerMessage;

        //  -----------  Making the input field grow till max width ------- //
        inputField.style.width = inputFieldWidth + 'px';
        let inputFieldDiv = L.DomUtil.get(this._inputField);

        // create invisible div to measure the text width in pixels
        let ruler = L.DomUtil.create('div', 'leaflet-popup-input-ruler', editScreen);
        let thisStandIn = this;

        // add event listener to the textinput to trigger a check
        this._inputField.addEventListener("keydown", function(){
        // Check to see if the popup is already at its maxWidth and that text doesnt take up whole field
            if (thisStandIn._container.offsetWidth < thisStandIn.options.maxWidth + 38
                && thisStandIn._inputFieldWidth + 5 < inputFieldDiv.clientWidth){
                ruler.innerHTML = inputField.innerHTML;

                if (ruler.offsetWidth + 20 > inputFieldDiv.clientWidth){
                console.log('expand now');
                inputField.style.width = thisStandIn._inputField.style.width = ruler.offsetWidth + 10 + 'px';
                thisStandIn.update();
                }
            }
        }, false);


        let inputActions = this._inputActions = L.DomUtil.create('div', 'leaflet-popup-input-actions', editScreen);

        let cancelButton = this._cancelButton = L.DomUtil.create('a', 'leaflet-popup-input-cancel', inputActions);
        cancelButton.href = '#cancel';
        cancelButton.innerHTML = 'Cancel';

        let imageLabel = this._imageLabel = L.DomUtil.create('label', 'leaflet-popup-label-image', inputActions);

        let imageUpload = this._imageUpload = L.DomUtil.create('input', 'leaflet-popup-upload-image', imageLabel);
        imageUpload.type = 'file';
        imageUpload.accept = '.jpg, .jpeg, .png';
        imageUpload.name = 'markerPhoto';
        imageUpload.style = 'display: none;'

        let imageButton = this._imageButton = L.DomUtil.create('a', 'leaflet-popup-input-image', imageLabel);
        imageButton.href = "#image";
        imageButton.innerHTML = 'Add Photo';

        let deleteImageButton = this._deleteImageButton = L.DomUtil.create('a', 'leaflet-popup-input-delete-image', inputActions);
        deleteImageButton.href = "#delete-image";
        deleteImageButton.innerHTML = 'Delete Photo';

        let saveButton = this._saveButton = L.DomUtil.create('a', 'leaflet-popup-input-save', inputActions);
        saveButton.href = "#save";
        saveButton.innerHTML = 'Save';

        L.DomEvent.on(cancelButton, 'click', this._onCancelButtonClick, this)
        L.DomEvent.on(imageButton, 'click', this._onAddImageButtonClick, this)
        L.DomEvent.on(deleteImageButton, 'click', this._onDeleteImageButton, this)
        L.DomEvent.on(saveButton, 'click', this._onSaveButtonClick, this)

        this.update();
        L.DomEvent.stop(e);
    },

    _onCancelButtonClick: function (e) {
        L.DomUtil.remove(this._editScreen);
        this._contentNode.style.display = "block";
        this._userActionButtons.style.display = "flex";

        this.update();
        L.DomEvent.stop(e);
    },

    _onDeleteImageButton: function (e) {
        elementActions = e.target.parentElement;
        elementEditScreen = elementActions.parentElement;
        elementContentWrapper = elementEditScreen.parentElement;
        elementContent = elementContentWrapper.querySelector('[class="leaflet-popup-content"]');
        imageEl = elementContent.querySelector('[name="imageEl"]');

        if (imageEl) {
            while (imageEl.firstChild) {
                imageEl.removeChild(imageEl.firstChild);
            }
        }

        this.options.markerPhoto = '';
        this.options.isDeletePhoto = true;
    },

    _onAddImageButtonClick: function (e) {
        elementLabel = e.target.parentElement;
        markerPhoto = elementLabel.querySelector('[name="markerPhoto"]');

        elementActions = elementLabel.parentElement;
        elementEditScreen = elementActions.parentElement;
        elementContentWrapper = elementEditScreen.parentElement;
        elementContent = elementContentWrapper.querySelector('[class="leaflet-popup-content"]');

        imageEl = elementContent.querySelector('[name="imageEl"]');

        if (!imageEl) {
            imageEl = document.createElement("div");
            imageEl.setAttribute('name', 'imageEl');
            elementContent.appendChild(imageEl);
        }

        markerPhoto.addEventListener(
            "change",
            (e) => {
                if (this._imageUpload.files.length > 0) {
                    imageEl.innerHTML = "";
                    const img = document.createElement("img");
                    img.classList.add('image-popup');
                    img.src = URL.createObjectURL(this._imageUpload.files[0]);
                    img.width = 250;
                    imageEl.appendChild(img);
                    this.options.markerPhoto = img.src;
                    this.options.isDeletePhoto = false;
                }
            },
            false,
        );

        markerPhoto.click();
    },

    _onSaveButtonClick: function (e) {
        if (this._inputField.innerHTML.length > 0) {
            this.options.markerMessage = this._inputField.innerHTML;
        };

        let popupContent = markerPopupData(
            this.options.markerTime,
            this.options.markerId,
            this.options.markerTelegramUsername,
            (this.getLatLng().lat).toFixed(5),
            (this.getLatLng().lng).toFixed(5),
            this.options.markerMessage,
            this.options.markerPhoto
        );

        this.setContent(popupContent);

        L.DomUtil.remove(this._editScreen);
        this._contentNode.style.display = "block";
        this._userActionButtons.style.display = "flex";

        this.update();
        L.DomEvent.stop(e);
    },

    _onSendButtonClick: function (e) {
        const formData = new FormData();
        let this_marker = this;
        let photo = '';

        formData.append('latitude', `${(this._latlng['lat']).toFixed(5)}`);
        formData.append('longitude', `${(this._latlng['lng']).toFixed(5)}`);
        formData.append('marker_id', this.options.markerId);
        formData.append('message', this.options.markerMessage);

        let isDeletePhoto = ('isDeletePhoto' in this.options && this.options.isDeletePhoto) ? true : false;

        formData.append('is_delete_photo', isDeletePhoto);

        if ('_imageUpload' in this && 'files' in this._imageUpload && this._imageUpload.files.length) {
            photo = this._imageUpload.files[0];
        };

        if (photo && !isDeletePhoto) {
            const reader = new FileReader();

            reader.onload = function(event) {
                const img = new Image();
                img.src = event.target.result;

                img.onload = function() {
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');

                    if (img.width > 800) {
                        const scaleFactor = 800 / img.width;
                        canvas.width = 800;
                        canvas.height = img.height * scaleFactor;
                    } else {
                        canvas.width = img.width;
                        canvas.height = img.height;
                    }

                    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

                    canvas.toBlob(function(blob) {
                        formData.append('photo', blob, photo.name);

                        if (this_marker.options.markerId) {
                            updateMarker(formData, this_marker.options.markerId);
                        } else {
                            createMarker(formData, this_marker);
                        };

                    }, photo.type);
                };
            };

            reader.readAsDataURL(photo);

        } else {
            if (this_marker.options.markerId) {
                updateMarker(formData, this_marker.options.markerId);
            } else {
                createMarker(formData, this_marker);
            };
        };

        if (this._editScreen) {
            L.DomUtil.remove(this._editScreen);
        };
        this._contentNode.style.display = "block";
        this._userActionButtons.style.display = "flex";

        this.update();
        L.DomEvent.stop(e);
    }

});


///////////// Cookie ///////////
function getCookie(name) {

    let matches = document.cookie.match(new RegExp(
      "(?:^|; )" + name.replace(/([.$?*|{}()[\]\\/+^])/g, '\\$1') + "=([^;]*)"
    ));

    return matches ? decodeURIComponent(matches[1]) : undefined;
}


function setCookie(name, value, options = {}) {

    options = {
        path: '/',
        // при необходимости добавьте другие значения по умолчанию
        ...options
    };

    if (options.expires instanceof Date) {
        options.expires = options.expires.toUTCString();
    }

    let updatedCookie = encodeURIComponent(name) + "=" + encodeURIComponent(value);

    for (let optionKey in options) {
        updatedCookie += "; " + optionKey;
        let optionValue = options[optionKey];

        if (optionValue !== true) {
            updatedCookie += "=" + optionValue;
        }
    }

    document.cookie = updatedCookie;
}


function deleteCookie(name) {
    setCookie(name, "", {
        'max-age': -1
    })
}
