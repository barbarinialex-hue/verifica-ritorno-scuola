document.addEventListener('submit', (event) => {
  const form = event.target;
  const message = form.dataset.confirm;
  if (message && !window.confirm(message)) {
    event.preventDefault();
    return;
  }

  const submitButton = form.querySelector('button[type="submit"]');
  if (submitButton && !form.matches('[enctype="multipart/form-data"]')) {
    submitButton.disabled = true;
    submitButton.dataset.originalLabel = submitButton.textContent;
    submitButton.textContent = 'Invio…';
  }
});

const reportMarkers = new Map();
const reportMaps = [];
document.querySelectorAll('[data-report-map]').forEach((element) => {
  if (!window.L) return;

  const points = JSON.parse(element.dataset.mapPoints || '[]');
  if (!points.length) return;

  const map = window.L.map(element, { scrollWheelZoom: false });
  window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    referrerPolicy: 'strict-origin-when-cross-origin',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>',
  }).addTo(map);

  const bounds = [];
  points.forEach((point) => {
    const position = [point.latitude, point.longitude];
    bounds.push(position);
    const marker = window.L.marker(position).addTo(map);
    const popup = document.createElement('div');
    if (point.image_url) {
      const photoButton = document.createElement('button');
      const image = document.createElement('img');
      photoButton.type = 'button';
      photoButton.className = 'map-popup-photo';
      photoButton.dataset.lightboxSrc = point.image_url;
      photoButton.dataset.lightboxAlt = `Foto della segnalazione: ${point.title}`;
      photoButton.dataset.lightboxGroup = 'map-popups';
      image.className = 'map-popup-image';
      image.src = point.image_url;
      image.alt = photoButton.dataset.lightboxAlt;
      image.loading = 'lazy';
      photoButton.append(image);
      popup.append(photoButton);
    }
    const title = document.createElement('strong');
    const metadata = document.createElement('p');
    const address = document.createElement('p');
    const link = document.createElement('a');
    title.textContent = point.title;
    metadata.textContent = `${point.status} · ${point.category}`;
    address.textContent = point.address;
    link.href = point.url;
    link.textContent = 'Apri segnalazione';
    popup.append(title, metadata, address, link);
    marker.bindPopup(popup);
    marker.on('click', () => {
      document.querySelectorAll('.report-row.is-map-focused').forEach((row) => row.classList.remove('is-map-focused'));
      const row = Array.from(document.querySelectorAll('[data-report-id]')).find((item) => item.dataset.reportId === String(point.id));
      row?.classList.add('is-map-focused');
    });
    if (point.id !== undefined) reportMarkers.set(String(point.id), { map, marker });
  });

  if (bounds.length === 1) map.setView(bounds[0], 15);
  else map.fitBounds(bounds, { padding: [28, 28], maxZoom: 15 });
  reportMaps.push(map);
});

const mobileViewButtons = Array.from(document.querySelectorAll('[data-mobile-view]'));
function setMobileView(view, scrollToPanel = false) {
  document.body.dataset.mobileView = view;
  mobileViewButtons.forEach((button) => {
    button.setAttribute('aria-pressed', String(button.dataset.mobileView === view));
  });
  reportMaps.forEach((map) => window.setTimeout(() => map.invalidateSize(), 0));
  if (scrollToPanel && window.matchMedia('(max-width: 767.98px)').matches) {
    document.querySelector(`[data-mobile-panel="${view}"]`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}
if (mobileViewButtons.length) {
  const mobileBreakpoint = window.matchMedia('(max-width: 767.98px)');
  setMobileView(mobileBreakpoint.matches ? 'list' : 'both');
  mobileViewButtons.forEach((button) => button.addEventListener('click', () => setMobileView(button.dataset.mobileView, true)));
  mobileBreakpoint.addEventListener('change', (event) => setMobileView(event.matches ? 'list' : 'both'));
}

document.querySelectorAll('[data-map-target]').forEach((button) => {
  button.addEventListener('click', () => {
    const location = reportMarkers.get(button.dataset.mapTarget);
    if (!location) return;
    document.querySelectorAll('.report-row.is-map-focused').forEach((row) => row.classList.remove('is-map-focused'));
    button.closest('[data-report-id]')?.classList.add('is-map-focused');
    setMobileView('map', true);
    if (!window.matchMedia('(max-width: 767.98px)').matches) {
      document.querySelector('[data-mobile-panel="map"]')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    window.setTimeout(() => {
      location.map.invalidateSize();
      location.map.setView(location.marker.getLatLng(), Math.max(location.map.getZoom(), 15));
      location.marker.openPopup();
    }, 0);
  });
});

const locationMapElement = document.querySelector('[data-location-map]');
if (locationMapElement) {
  const latitudeInput = document.querySelector('#latitudine');
  const longitudeInput = document.querySelector('#longitudine');
  const addressInput = document.querySelector('#indirizzo');
  const locationStatus = document.querySelector('[data-location-status]');
  if (!window.L) {
    locationStatus.textContent = 'Mappa non disponibile. Inserisci le coordinate manualmente.';
  } else {
    const map = window.L.map(locationMapElement, { scrollWheelZoom: false });
    window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      referrerPolicy: 'strict-origin-when-cross-origin',
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>',
    }).addTo(map);
    const initialLatitude = Number(latitudeInput.value);
    const initialLongitude = Number(longitudeInput.value);
    const hasInitialPoint = Number.isFinite(initialLatitude) && Number.isFinite(initialLongitude)
      && latitudeInput.value !== '' && longitudeInput.value !== '';
    const initialPosition = hasInitialPoint ? [initialLatitude, initialLongitude] : [42.5, 12.5];
    map.setView(initialPosition, hasInitialPoint ? 15 : 6);
    let marker = hasInitialPoint ? window.L.marker(initialPosition, { draggable: true }).addTo(map) : null;

    const setLocation = (latitude, longitude, zoom = 16, message = 'Posizione selezionata.') => {
      const position = [latitude, longitude];
      latitudeInput.value = latitude.toFixed(6);
      longitudeInput.value = longitude.toFixed(6);
      if (marker) marker.setLatLng(position);
      else marker = window.L.marker(position, { draggable: true }).addTo(map);
      marker.off('dragend');
      marker.on('dragend', (event) => {
        const moved = event.target.getLatLng();
        latitudeInput.value = moved.lat.toFixed(6);
        longitudeInput.value = moved.lng.toFixed(6);
      });
      map.setView(position, zoom);
      locationStatus.textContent = message;
    };

    if (marker) {
      marker.on('dragend', (event) => {
        const moved = event.target.getLatLng();
        latitudeInput.value = moved.lat.toFixed(6);
        longitudeInput.value = moved.lng.toFixed(6);
      });
    }
    map.on('click', (event) => setLocation(event.latlng.lat, event.latlng.lng));
    [latitudeInput, longitudeInput].forEach((input) => input.addEventListener('change', () => {
      const latitude = Number(latitudeInput.value);
      const longitude = Number(longitudeInput.value);
      if (Number.isFinite(latitude) && Number.isFinite(longitude)) setLocation(latitude, longitude, map.getZoom());
    }));

    document.querySelector('[data-geolocate]')?.addEventListener('click', () => {
      if (!navigator.geolocation) {
        locationStatus.textContent = 'La geolocalizzazione non è disponibile in questo browser.';
        return;
      }
      locationStatus.textContent = 'Rilevamento posizione…';
      navigator.geolocation.getCurrentPosition(
        ({ coords }) => setLocation(coords.latitude, coords.longitude, 16, 'Posizione corrente selezionata.'),
        () => { locationStatus.textContent = 'Posizione non disponibile. Cerca un indirizzo o seleziona la mappa.'; },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
      );
    });

    let lastGeocodeRequest = 0;
    document.querySelector('[data-geocode]')?.addEventListener('click', async (event) => {
      const query = addressInput.value.trim();
      if (!query) {
        locationStatus.textContent = 'Inserisci prima un indirizzo.';
        addressInput.focus();
        return;
      }
      const button = event.currentTarget;
      button.disabled = true;
      locationStatus.textContent = 'Ricerca indirizzo…';
      try {
        const wait = Math.max(0, 1000 - (Date.now() - lastGeocodeRequest));
        if (wait) await new Promise((resolve) => window.setTimeout(resolve, wait));
        lastGeocodeRequest = Date.now();
        const url = new URL('https://nominatim.openstreetmap.org/search');
        url.search = new URLSearchParams({ q: query, format: 'jsonv2', limit: '1', countrycodes: 'it' });
        const response = await fetch(url, { headers: { 'Accept-Language': 'it' } });
        if (!response.ok) throw new Error('Ricerca non disponibile');
        const results = await response.json();
        if (!results.length) {
          locationStatus.textContent = 'Indirizzo non trovato. Prova a precisarlo o scegli il punto sulla mappa.';
          return;
        }
        const result = results[0];
        setLocation(Number(result.lat), Number(result.lon), 16, `Trovato: ${result.display_name}`);
      } catch {
        locationStatus.textContent = 'Ricerca non riuscita. Puoi selezionare il punto direttamente sulla mappa.';
      } finally {
        button.disabled = false;
      }
    });
  }
}

const imageViewer = document.querySelector('#imageViewerModal');
const imageViewerImage = document.querySelector('#imageViewerImage');
const imageViewerCount = document.querySelector('#imageViewerCount');
let imageGallery = [];
let imageGalleryIndex = 0;
function showViewerImage() {
  const current = imageGallery[imageGalleryIndex];
  if (!current) return;
  imageViewerImage.src = current.dataset.lightboxSrc;
  imageViewerImage.alt = current.dataset.lightboxAlt || '';
  imageViewerCount.textContent = imageGallery.length > 1 ? `${imageGalleryIndex + 1} / ${imageGallery.length}` : '';
  imageViewer.querySelector('[data-viewer-prev]').hidden = imageGallery.length < 2;
  imageViewer.querySelector('[data-viewer-next]').hidden = imageGallery.length < 2;
}
document.addEventListener('click', (event) => {
  const trigger = event.target.closest('[data-lightbox-src]');
  if (!trigger || !trigger.dataset.lightboxSrc || !imageViewer || !window.bootstrap) return;
  event.preventDefault();
  const group = trigger.dataset.lightboxGroup;
  imageGallery = Array.from(document.querySelectorAll('[data-lightbox-src]'))
    .filter((item) => item.dataset.lightboxGroup === group && item.dataset.lightboxSrc);
  imageGalleryIndex = imageGallery.indexOf(trigger);
  showViewerImage();
  window.bootstrap.Modal.getOrCreateInstance(imageViewer).show();
});
imageViewer?.querySelector('[data-viewer-prev]')?.addEventListener('click', () => {
  imageGalleryIndex = (imageGalleryIndex - 1 + imageGallery.length) % imageGallery.length;
  showViewerImage();
});
imageViewer?.querySelector('[data-viewer-next]')?.addEventListener('click', () => {
  imageGalleryIndex = (imageGalleryIndex + 1) % imageGallery.length;
  showViewerImage();
});
imageViewer?.addEventListener('keydown', (event) => {
  if (event.key === 'ArrowLeft' && imageGallery.length > 1) imageViewer.querySelector('[data-viewer-prev]').click();
  if (event.key === 'ArrowRight' && imageGallery.length > 1) imageViewer.querySelector('[data-viewer-next]').click();
});

const imageInput = document.querySelector('#immagine');
const imagePreview = document.querySelector('[data-image-preview]');
if (imageInput && imagePreview) {
  let previewUrl;
  imageInput.addEventListener('change', () => {
    const [file] = imageInput.files;
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    if (!file) {
      imagePreview.hidden = true;
      return;
    }
    previewUrl = URL.createObjectURL(file);
    imagePreview.querySelector('[data-image-preview-img]').src = previewUrl;
    imagePreview.querySelector('[data-image-preview-name]').textContent = file.name;
    imagePreview.hidden = false;
  });
}

const cookieNotice = document.querySelector('[data-cookie-notice]');
if (cookieNotice && localStorage.getItem('technical-cookie-notice') !== 'dismissed') {
  cookieNotice.hidden = false;
}

document.querySelector('[data-cookie-dismiss]')?.addEventListener('click', () => {
  localStorage.setItem('technical-cookie-notice', 'dismissed');
  cookieNotice.hidden = true;
});
