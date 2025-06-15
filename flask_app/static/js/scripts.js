// Nous enveloppons tout le code dans DOMContentLoaded pour s'assurer que le DOM est chargé.
document.addEventListener('DOMContentLoaded', function() {
  // Sauvegarde des fonctions console d'origine
  const originalConsoleLog = console.log;
  const originalConsoleWarn = console.warn;
  const originalConsoleError = console.error;
  
  function sendClientLog(level, args) {
    const logData = {
      level: level,
      messages: args,
      timestamp: new Date().toISOString()
    };
    fetch('/client-log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(logData)
    }).catch(err => {
      originalConsoleError('[ERROR] Échec de l\'envoi du log au serveur:', err);
    });
  }
  
  // Redéfinition des fonctions console pour logger également sur le serveur
  console.log = function(...args) {
    originalConsoleLog.apply(console, args);
    sendClientLog('log', args);
  };
  
  console.warn = function(...args) {
    originalConsoleWarn.apply(console, args);
    sendClientLog('warn', args);
  };
  
  console.error = function(...args) {
    originalConsoleError.apply(console, args);
    sendClientLog('error', args);
  };

  // Déclaration de variables globales pour les graphiques et l'itinéraire
  let barChart, pieChart;
  let clickedPoints = [];         // stocke jusqu'à 2 points cliqués pour l'itinéraire
  let itineraireTotalDistance = 0;  // distance totale du dernier itinéraire (mètres)
  let isItineraireActive = false;

  // Initialisation des couches WMS existantes
  const wmsLayerQuartier = new ol.layer.Image({
    source: new ol.source.ImageWMS({
      url: 'http://localhost:8085/geoserver/wms',
      params: { 'LAYERS': 'vm_iris_indicateur', 'FORMAT': 'image/png' },
      serverType: 'geoserver'
    }),
    opacity: 0.5,
    visible: true
  });
  
  const wmsLayerTroncon = new ol.layer.Image({
    source: new ol.source.ImageWMS({
      url: 'http://localhost:8085/geoserver/wms',
      params: { 'LAYERS': 'troncon_cheminement', 'FORMAT': 'image/png' },
      serverType: 'geoserver'
    }),
    visible: true
  });
  
  const wmsLayerLignebus = new ol.layer.Image({
    source: new ol.source.ImageWMS({
      url: 'http://localhost:8085/geoserver/wms',
      params: { 'LAYERS': 'ligne', 'FORMAT': 'image/png' },
      serverType: 'geoserver'
    }),
    visible: false
  });
  
  const wmsLayerArretbus = new ol.layer.Image({
    source: new ol.source.ImageWMS({
      url: 'http://localhost:8085/geoserver/wms',
      params: { 'LAYERS': 'arret', 'FORMAT': 'image/png' },
      serverType: 'geoserver'
    }),
    visible: false
  });
  
  const wmsLayerErp = new ol.layer.Image({
    source: new ol.source.ImageWMS({
      url: 'http://localhost:8085/geoserver/wms',
      params: { 'LAYERS': 'erp', 'FORMAT': 'image/png' },
      serverType: 'geoserver'
    }),
    visible: false
  });
  
  const wmsLayerStationnementpmr = new ol.layer.Image({
    source: new ol.source.ImageWMS({
      url: 'http://localhost:8085/geoserver/wms',
      params: { 'LAYERS': 'stationnement_pmr', 'FORMAT': 'image/png' },
      serverType: 'geoserver'
    }),
    visible: false
  });
  
  const wmsLayerTravaux = new ol.layer.Image({
    source: new ol.source.ImageWMS({
      url: 'http://localhost:8085/geoserver/wms',
      params: { 'LAYERS': 'travaux', 'FORMAT': 'image/png' },
      serverType: 'geoserver'
    }),
    visible: false
  });
  
  // Initialisation de la carte OpenLayers et des couches
  const map = new ol.Map({
    target: 'map',
    layers: [
      new ol.layer.Tile({ source: new ol.source.OSM() }),
      wmsLayerQuartier,
      wmsLayerTroncon,
      wmsLayerLignebus,   
      wmsLayerArretbus,   
      wmsLayerErp,
      wmsLayerStationnementpmr,
      wmsLayerTravaux     
    ],
    view: new ol.View({
      center: ol.proj.fromLonLat([4.8357, 45.7640]),
      zoom: 12
    })
  });

  // Fonction utilitaire pour masquer toutes les popups dédiées
  function hideAllPopups() {
    document.getElementById('popup-quartier').style.display = "none";
    document.getElementById('popup-troncon').style.display = "none";
    document.getElementById('popup-legend').style.display = "none";
    document.getElementById('popup-itineraire').style.display = "none";
  }
  
  // Gestion du clic sur la carte
  map.on('singleclick', function (evt) {
    // Masque toutes les popups dédiées
    hideAllPopups();
    
    if (wmsLayerQuartier.getVisible()) {
      const viewResolution = map.getView().getResolution();
      const coordinate = evt.coordinate;
      const url = wmsLayerQuartier.getSource().getFeatureInfoUrl(
        coordinate,
        viewResolution,
        'EPSG:3857',
        { 'INFO_FORMAT': 'application/json' }
      );
      if (url) {
        fetch(url)
          .then(response => response.json())
          .then(data => {
            if (data.features && data.features.length > 0) {
              const properties = data.features[0].properties;
              let content = '<b>Quartier :</b><br>';
              content += `Nom: ${properties['nom_iris']}<br>`;
              content += `Nombre d'habitants: ${formatValue(properties['population_iris'], 'integer')}<br>`;
              content += `Accessibilité: ${formatValue(properties['pourcent_access'], 'percent')}<br>`;
              content += `Accessibilité moyenne: ${formatValue(properties['pourcent_access_moy'], 'percent')}<br>`;
              content += `Non accessible: ${formatValue(properties['pourcent_non_access'], 'percent')}<br>`;
              content += `Voie accessible: ${formatValue(properties['lg_accessible'], 'meter')}<br>`;
              content += `Voie accessibilité moyenne: ${formatValue(properties['lg_access_moy'], 'meter')}<br>`;
              content += `Voie non accessible: ${formatValue(properties['lg_non_access'], 'meter')}<br>`;
              content += `Indicateur: ${formatValue(properties['indicateur'], 'decimal')}<br>`;
              const popupQuart = document.getElementById('popup-quartier');
              popupQuart.innerHTML = content;
              popupQuart.style.left = evt.pixel[0] + 'px';
              popupQuart.style.top = evt.pixel[1] + 'px';
              popupQuart.style.display = 'block';
              // Mise à jour des graphiques avec les données du quartier cliqué
              updateCharts(properties);
            } else {
              document.getElementById('popup-quartier').style.display = 'none';
            }
          })
          .catch(err => {
            console.error('Erreur lors de la récupération des données (Quartier) :', err);
            document.getElementById('popup-quartier').style.display = 'none';
          });
      }
    } else if (wmsLayerTroncon.getVisible()) {
      const viewResolution = map.getView().getResolution();
      const coordinate = evt.coordinate;
      const url = wmsLayerTroncon.getSource().getFeatureInfoUrl(
        coordinate,
        viewResolution,
        'EPSG:3857',
        { 'INFO_FORMAT': 'application/json' }
      );
      if (url) {
        fetch(url)
          .then(response => response.json())
          .then(data => {
            if (data.features && data.features.length > 0) {
              const properties = data.features[0].properties;
              let content = '<b>Tronçon cheminement</b><br>';
              content += `Type: ${properties['typtroncon']}<br>`;
              content += `Statut de la voie: ${properties['statutvoie']}<br>`;
              content += `Largeur: ${properties['largeur']} m<br>`;
              content += `Pente: ${properties['pente']} %<br>`;
              content += `Dévers: ${properties['devers']} %<br>`;
              content += `Accessibilité: ${properties['accessibiliteglobale']}<br>`;
              const popupTron = document.getElementById('popup-troncon');
              popupTron.innerHTML = content;
              popupTron.style.left = evt.pixel[0] + 'px';
              popupTron.style.top = evt.pixel[1] + 'px';
              popupTron.style.display = 'block';
            } else {
              document.getElementById('popup-troncon').style.display = 'none';
            }
          })
          .catch(err => {
            console.error('Erreur lors de la récupération des données (Tronçon) :', err);
            document.getElementById('popup-troncon').style.display = 'none';
          });
      }
    } else {
      hideAllPopups();
    }
    
    // Gestion de l'itinéraire automatique
    if (isItineraireActive) {
      if (clickedPoints.length === 0) {
        routingMarkerLayer.getSource().clear(); // Supprime tous les anciens marqueurs
        itineraireLayer.getSource().clear();      // Supprime le tracé précédent
      }
  
      if (clickedPoints.length < 2) {
        clickedPoints.push(evt.coordinate);
  
        // Création d'un marqueur sur la carte
        createMarker(evt.coordinate);
        if (clickedPoints.length === 2) {
          fetchNearestNodesAndGetRoute(clickedPoints[0], clickedPoints[1]);
        }
      }
    }
  });
  
  // Fonction utilitaire de formatage
  function formatValue(value, type) {
    if (type === 'integer') {
      return Math.round(value);
    } else if (type === 'percent') {
      return Math.round(value) + ' %';
    } else if (type === 'meter') {
      return Math.round(value) + ' m';
    } else if (type === 'decimal') {
      return value.toFixed(2);
    }
    return value;
  }
  
  // Fonction qui met à jour les graphiques en utilisant les propriétés du quartier cliqué
  function updateCharts(properties) {
    if (barChart) {
      barChart.data.datasets[0].data = [
        parseFloat((properties['lg_accessible'] / 1000).toFixed(2)),
        parseFloat((properties['lg_access_moy'] / 1000).toFixed(2)),
        parseFloat((properties['lg_non_access'] / 1000).toFixed(2))
      ];
      barChart.update();
    }
    if (pieChart) {
      pieChart.data.datasets[0].data = [
        Math.round(properties['pourcent_access']),
        Math.round(properties['pourcent_access_moy']),
        Math.round(properties['pourcent_non_access'])
      ];
      pieChart.update();
    }
  }
  
  // Gestion des boutons de bascule des couches WMS
  // Bouton Accessibilité par quartier pour wmsLayerQuartier
  document.getElementById('toggle-wms-quartier').addEventListener('click', function() {
    console.log(`[INFO] Bouton "Accessibilité par quartier" cliqué à ${new Date().toISOString()} - Couche Accessibilité par quartier visible: ${visible}`);
    const visible = wmsLayerQuartier.getVisible();
    wmsLayerQuartier.setVisible(!visible);
    console.log(`[INFO] Couche Accessibilité par quartier devient ${!visible ? 'visible' : 'masquée'}`);
  });
  
  // Bouton Tronçon d'accessibilité pour wmsLayerTroncon
  document.getElementById('toggle-wms-troncon').addEventListener('click', function() {
    const visible = wmsLayerTroncon.getVisible();
    console.log(`[INFO] Bouton "Tronçon d'accessibilité" cliqué à ${new Date().toISOString()} - Couche Tronçon d'accessibilité visible: ${visible}`);
    wmsLayerTroncon.setVisible(!visible);
    console.log(`[INFO] Couche Tronçon d'accessibilité devient ${!visible ? 'visible' : 'masquée'}`);
  });
  
  // Bouton Transport pour wmsLayerArretbus et wmsLayerLignebus
  document.getElementById('toggle-wms-transport').addEventListener('click', function() {
    const isVisible = wmsLayerArretbus.getVisible() && wmsLayerLignebus.getVisible();
    console.log(`[INFO] Bouton "Transport" cliqué à ${new Date().toISOString()} - Couche Transport visible: ${visible}`);
    wmsLayerArretbus.setVisible(!isVisible);
    wmsLayerLignebus.setVisible(!isVisible);
    console.log(`[INFO] Couche Transport devient ${!visible ? 'visible' : 'masquée'}`);
  });
  
  // Bouton ERP pour wmsLayerErp
  document.getElementById('toggle-wms-erp').addEventListener('click', function() {
    const visible = wmsLayerErp.getVisible();
    console.log(`[INFO] Bouton "ERP" cliqué à ${new Date().toISOString()} - Couche ERP visible: ${visible}`);
    wmsLayerErp.setVisible(!visible);
    console.log(`[INFO] Couche ERP devient ${!visible ? 'visible' : 'masquée'}`);
  });
  
  // Bouton Travaux pour wmsLayerTravaux
  document.getElementById('toggle-wms-travaux').addEventListener('click', function() {
    const visible = wmsLayerTravaux.getVisible();
    console.log(`[INFO] Bouton "Travaux" cliqué à ${new Date().toISOString()} - Couche Travaux visible: ${visible}`);
    wmsLayerTravaux.setVisible(!visible);
    console.log(`[INFO] Couche Travaux devient ${!visible ? 'visible' : 'masquée'}`);
  });
  
  // Bouton PMR pour wmsLayerStationnementpmr
  document.getElementById('toggle-wms-pmr').addEventListener('click', function() {
    const visible = wmsLayerStationnementpmr.getVisible();
    console.log(`[INFO] Bouton "PMR" cliqué à ${new Date().toISOString()} - Couche Stationnement PMR visible: ${visible}`);
    wmsLayerStationnementpmr.setVisible(!visible);
    console.log(`[INFO] Couche Stationnement PMR devient ${!visible ? 'visible' : 'masquée'}`);
  });
  
  window.addEventListener('load', () => {
    map.updateSize();
    console.log(`[INFO] Événement "load" déclenché - Mise à jour de la taille de la carte effectuée`);
  });
  window.addEventListener('resize', () => {
    map.updateSize();
    console.log(`[INFO] Événement "resize" déclenché - Nouvelle taille de la carte recalculée`);
  });
  
  // Initialisation des graphiques par défaut à partir des données récupérées
  fetch('/get_accessibility_data')
    .then(response => response.json())
    .then(data => {
      console.log(`[INFO] Données d'accessibilité récupérées :`, data);
      // Formatage des valeurs pour l'histogramme en km avec 2 chiffres après la virgule
      const barData = {
        lg_accessible: parseFloat((data.lg_accessible / 1000).toFixed(2)),
        lg_access_moy: parseFloat((data.lg_access_moy / 1000).toFixed(2)),
        lg_non_access: parseFloat((data.lg_non_access / 1000).toFixed(2))
      };
      // Création de l'histogramme
      const ctx = document.getElementById('accessibilityChart').getContext('2d');
      barChart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: ['Accessible', 'Accessibilité Moyenne', 'Non Accessible'],
          datasets: [{
            label: 'Accessibilité des tronçons',
            data: [barData.lg_accessible, barData.lg_access_moy, barData.lg_non_access],
            backgroundColor: ['green', 'yellow', 'red'],
            borderColor: ['black', 'black', 'black'],
            borderWidth: 1,
            minBarLength: 5  // Assure une longueur minimale pour les petites valeurs
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          onResize: function(chart, size) {
            const newSize = size.width;
            const fontSize = Math.min(Math.max(newSize / 40, 10), 18);
            chart.options.plugins.legend.labels.font.size = fontSize;
          },
          indexAxis: 'y',
          scales: {
            x: { 
              beginAtZero: true,
              ticks: {
                callback: function(value) {
                  return Number(value).toFixed(2);
                }
              }
            }
          },
          plugins: {
            legend: {
              display: true,
              position: 'bottom',
              labels: {
                font: { size: 14, weight: 'bold' },
                generateLabels: function(chart) {
                  const data = chart.data;
                  if (data.labels.length && data.datasets.length) {
                    return data.labels.map(function(label, i) {
                      const ds = data.datasets[0];
                      return {
                        text: label,
                        fillStyle: ds.backgroundColor[i],
                        strokeStyle: ds.borderColor ? ds.borderColor[i] : '#000',
                        lineWidth: ds.borderWidth,
                        hidden: false,
                        index: i
                      };
                    });
                  }
                  return [];
                }
              }
            },
            tooltip: { enabled: true },
            title: {
              display: true,
              text: 'Km de tronçons accessibles',
              font: { size: 16, weight: 'bold' }
            }
          }
        }
      });
      console.log(`[INFO] Histogramme (barChart) initialisé`);
  
      // Création du graphique en camembert
      const pieData = {
        pourcent_access: Math.round(data.pourcent_access),
        pourcent_access_moy: Math.round(data.pourcent_access_moy),
        pourcent_non_access: Math.round(data.pourcent_non_access)
      };
  
      const pieCtx = document.getElementById('accessibilityPieChart').getContext('2d');
      pieChart = new Chart(pieCtx, {
        type: 'pie',
        data: {
          labels: ['Accessible', 'Accessibilité Moyenne', 'Non Accessible'],
          datasets: [{
            data: [pieData.pourcent_access, pieData.pourcent_access_moy, pieData.pourcent_non_access],
            backgroundColor: ['green', 'yellow', 'red'],
            borderColor: ['black', 'black', 'black'],
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          onResize: function(chart, size) {
            const newSize = size.width;
            const fontSize = Math.min(Math.max(newSize / 40, 10), 18);
            chart.options.plugins.legend.labels.font.size = fontSize;
          },
          plugins: {
            legend: {
              display: true,
              position: 'bottom',
              labels: {
                font: { size: 14, weight: 'bold' },
                generateLabels: function(chart) {
                  const data = chart.data;
                  if (data.labels.length && data.datasets.length) {
                    return data.labels.map(function(label, i) {
                      const ds = data.datasets[0];
                      return {
                        text: label,
                        fillStyle: ds.backgroundColor[i],
                        strokeStyle: ds.borderColor ? ds.borderColor[i] : '#000',
                        lineWidth: ds.borderWidth,
                        hidden: false,
                        index: i
                      };
                    });
                  }
                  return [];
                }
              }
            },
            tooltip: {
              enabled: true,
              callbacks: {
                label: function(context) {
                  const label = context.label || '';
                  const value = context.raw || 0;
                  return `${label}: ${value}%`;
                }
              }
            },
            title: {
              display: true,
              text: '% accessibilité',
              font: { size: 16, weight: 'bold' }
            }
          }
        }
      });
      console.log(`[INFO] Graphique en camembert (pieChart) initialisé`);
    })
    .catch(error => console.error('Erreur lors de la récupération des données:', error));
  
  // Fonction pour appeler l'API Flask et tracer l'itinéraire entre deux coordonnées (format EPSG:3857)
  function fetchNearestNodesAndGetRoute(coordStart, coordEnd) {
    fetch('/api/itineraire_coord', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        start: ol.proj.toLonLat(coordStart),
        end: ol.proj.toLonLat(coordEnd)
      })
    })
      .then(response => {
        if (!response.ok) {
          if (response.status === 404) {
            alert("Aucun itinéraire trouvé entre les deux points.");
          } else {
            alert("Erreur lors du calcul de l’itinéraire.");
          }
          resetItineraire();
          return null;
        }
        return response.json();
      })
      .then(geojson => {
        if (!geojson) return;
        const format = new ol.format.GeoJSON();
        const features = format.readFeatures(geojson, {
          dataProjection: 'EPSG:3857',
          featureProjection: 'EPSG:3857'
        });
        itineraireTotalDistance = geojson.features.reduce((sum, feat) => sum + (feat.properties.cost || 0), 0);
        const tempsMinutes = (itineraireTotalDistance / 1000) / 5 * 60;
        itineraireLayer.getSource().clear();
        itineraireLayer.getSource().addFeatures(features);
        map.getView().fit(itineraireLayer.getSource().getExtent(), { duration: 1000, padding: [50, 50, 50, 50] });
        
        const routeCenter = ol.extent.getCenter(itineraireLayer.getSource().getExtent());
        const pixel = map.getPixelFromCoordinate(routeCenter);
        const popupItine = document.getElementById('popup-itineraire');
        popupItine.innerHTML = `<b>Distance :</b> ${itineraireTotalDistance.toFixed(1)} m<br><b>Temps estimé :</b> ${tempsMinutes.toFixed(1)} min`;
        popupItine.style.left = pixel[0] + 'px';
        popupItine.style.top = pixel[1] + 'px';
        popupItine.style.display = 'block';
        setTimeout(() => {
          popupItine.style.display = 'none';
        }, 5000);
        clickedPoints = [];
      })
      .catch(err => {
        alert("Erreur lors du calcul automatique d’itinéraire.");
        console.error(err);
        clickedPoints = [];
      });
  }
  
  // Fonction de géocodage d'une adresse en coordonnées (via l'API Nominatim d'OpenStreetMap)
  function geocodeAdresse(adresse) {
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(adresse)}`;
    return fetch(url, { headers: { 'User-Agent': 'access-leg-app' } })
      .then(res => res.json())
      .then(data => {
        if (data.length === 0) throw new Error("Adresse introuvable");
        return [parseFloat(data[0].lon), parseFloat(data[0].lat)];
      });
  }
  
  // Fonction pour calculer un itinéraire à partir des adresses saisies dans le panneau
  function itineraireParAdresse() {
    const adresseDepart = document.getElementById('adresseDepart').value;
    const adresseArrivee = document.getElementById('adresseArrivee').value;
  
    if (!adresseDepart || !adresseArrivee) {
      alert("Veuillez remplir les deux adresses.");
      return;
    }
    resetItineraire();
  
    Promise.all([
      geocodeAdresse(adresseDepart),
      geocodeAdresse(adresseArrivee)
    ])
      .then(([coordDep, coordArr]) => {
        const coordStart = ol.proj.fromLonLat(coordDep);
        const coordEnd = ol.proj.fromLonLat(coordArr);
        fetchNearestNodesAndGetRoute(coordStart, coordEnd);
      })
      .catch(err => {
        alert("Erreur de géocodage : " + err.message);
      });
  }
  
  // Fonction pour fermer le panneau d'itinéraire et réinitialiser l'itinéraire
  function closeItinerairePanel() {
    const panel = document.getElementById("itineraire-panel");
    panel.style.display = "none";
    isItineraireActive = false;
    resetItineraire();
    console.log(`[DEBUG] Itinéraire panel display: ${panel.style.display}`);
  }
  
  // Fonction pour afficher/masquer le panneau d'itinéraire
  function toggleItineraire() {
    const panel = document.getElementById("itineraire-panel");
    if (panel.style.display === "none") {
      panel.style.display = "block";
      isItineraireActive = true;
    } else {
      panel.style.display = "none";
      isItineraireActive = false;
      resetItineraire();
    }
    console.log(`[DEBUG] Itinéraire panel display: ${panel.style.display}`);
  }
  
  // Activation de l'autocomplétion pour les champs d'adresse (appel à l'API Nominatim à chaque saisie)
  function autocompleteAdresse(inputId, datalistId) {
    const input = document.getElementById(inputId);
    const datalist = document.getElementById(datalistId);
    input.addEventListener("input", () => {
      const query = input.value;
      if (query.length < 3) return;
      fetch(`https://nominatim.openstreetmap.org/search?format=json&limit=5&q=${encodeURIComponent(query)}`, {
        headers: { 'User-Agent': 'access-leg-app' }
      })
        .then(response => response.json())
        .then(data => {
          datalist.innerHTML = "";
          data.forEach(place => {
            const option = document.createElement("option");
            option.value = place.display_name;
            datalist.appendChild(option);
          });
        });
    });
  }
  
  autocompleteAdresse("adresseDepart", "suggestionsDepart");
  autocompleteAdresse("adresseArrivee", "suggestionsArrivee");
  
  // Fonction pour réinitialiser/effacer l'itinéraire en cours
  function resetItineraire() {
    itineraireLayer.getSource().clear();
    routingMarkerLayer.getSource().clear();
    clickedPoints = [];
    const popup = document.getElementById('popup-itineraire');
    if (popup) popup.style.display = 'none';
    hideAllPopups();
  }
  
  // Fonction utilitaire pour créer un marqueur sur la carte à la position donnée
  function createMarker(coordinate) {
    const feature = new ol.Feature({
      geometry: new ol.geom.Point(coordinate)
    });
    routingMarkerLayer.getSource().addFeature(feature);
  }
  
  // Création des couches vectorielles pour l'itinéraire et les marqueurs de départ/arrivée
  const itineraireLayer = new ol.layer.Vector({
    source: new ol.source.Vector(),
    style: new ol.style.Style({
      stroke: new ol.style.Stroke({
        color: 'blue',
        width: 6,
        lineDash: [5, 10]  // tracé bleu en pointillés
      })
    })
  });
  map.addLayer(itineraireLayer);
  
  const routingMarkerLayer = new ol.layer.Vector({
    source: new ol.source.Vector(),
    style: new ol.style.Style({
      image: new ol.style.Icon({
        anchor: [0.5, 1],
        src: 'https://openlayers.org/en/latest/examples/data/icon.png'
      })
    })
  });
  map.addLayer(routingMarkerLayer);
  
  // Exemple de requête vers l'API Flask pour tester le calcul d'itinéraire
  fetch('http://localhost:5000/api/itineraire_coord', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      start: [4.835, 45.758],
      end: [4.84, 45.76]
    })
  })
    .then(res => res.json())
    .then(console.log)
    .catch(console.error);
  
  // Ajout des écouteurs d'événements pour remplacer les attributs onclick
  document.getElementById('goHomeButton').addEventListener('click', goHome);
  document.getElementById('showLegendButton').addEventListener('click', showLegend);
  document.getElementById('toggleItineraireButton').addEventListener('click', toggleItineraire);
  document.getElementById('itineraireCalcBtn').addEventListener('click', itineraireParAdresse);
  document.getElementById('closeItinerairePanelButton').addEventListener('click', closeItinerairePanel);
  
  // Fonction pour recentrer la carte sur la vue d'accueil
  function goHome() {
    map.getView().setCenter(ol.proj.fromLonLat([4.8357, 45.7640]));
    map.getView().setZoom(12);
  }
  
  // Fonction pour afficher la légende dans une popup dédiée
  function showLegend() {
    hideAllPopups();
    let content = '<h3>Légende</h3>';
    legendLayers.forEach(item => {
      if (item.layer.getVisible()) {
        let legendUrl = 'http://localhost:8085/geoserver/wms?REQUEST=GetLegendGraphic&VERSION=1.0.0&FORMAT=image/png&LAYER=' + item.name;
        content += '<div style="margin-bottom:10px;">';
        content += '<strong>' + item.title + ':</strong><br>';
        content += '<img src="' + legendUrl + '" alt="Légende ' + item.title + '">';
        content += '</div>';
        console.log(`[INFO] Ajout de la légende pour ${item.title} (URL: ${legendUrl})`);
      }
    });
    
    if (content === '<h3>Légende</h3>') {
      content += 'Aucune couche visible pour afficher la légende.';
      console.warn('[WARN] Aucune couche visible lors de l’affichage de la légende.');
    }
    
    const popupLegend = document.getElementById('popup-legend');
    popupLegend.innerHTML = content;
    popupLegend.style.left = "50%";
    popupLegend.style.top = "20px";
    popupLegend.style.transform = "translateX(-50%)";
    popupLegend.style.display = "block";
    console.log(`[INFO] Légende affichée à ${new Date().toISOString()}`);
  }
  
  // Tableau global pour la légende
  const legendLayers = [
    { layer: wmsLayerQuartier, name: 'vm_iris_indicateur', title: 'Quartiers' },
    { layer: wmsLayerTroncon, name: 'troncon_cheminement', title: 'Tronçon cheminement' },
    { layer: wmsLayerLignebus, name: 'ligne', title: 'Ligne bus' },
    { layer: wmsLayerArretbus, name: 'arret', title: 'Arrêt bus' },
    { layer: wmsLayerErp, name: 'erp', title: 'ERP' },
    { layer: wmsLayerStationnementpmr, name: 'stationnement_pmr', title: 'Stationnement PMR' },
    { layer: wmsLayerTravaux, name: 'travaux', title: 'Travaux' }
  ];



// Script log authentificatification de logging.html */

    // Vérifie si l'on est sur la page d'authentification
  if (document.body.classList.contains('logging-page')) {
      console.log("Page de login détectée.");

      const loginButton = document.getElementById('login-button');
      if (loginButton) {
          loginButton.addEventListener('click', function(event) {
              console.log("Bouton d'envoi du formulaire cliqué.");                
          });
      }
  }


// Comportement spécifique à la page de création de compte (logging_new.html)


  if (document.body.classList.contains('logging-new-page')) {
      console.log("Page de création de compte détectée.");
      const registerForm = document.getElementById('register-form');
      if (registerForm) {
          // Attacher l'événement submit pour valider le formulaire
          registerForm.addEventListener('submit', function(event) {
              const emailInput = document.getElementById("email").value;
              const pwdInput = document.getElementById("pwd").value;
              const pwdConfirmInput = document.getElementById("pwdConfirm").value;

              // Vérifier le format de l'adresse e-mail
              const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
              if (!emailRegex.test(emailInput)) {
                  alert("Adresse incorrecte, renseignez à nouveau");
                  event.preventDefault();
                  return false;
              }

              // Vérifier que les mots de passe sont identiques
              if (pwdInput !== pwdConfirmInput) {
                  alert("Mots de passe différents, recommencez");
                  event.preventDefault();
                  return false;
              }

              // Si tout est OK, le formulaire est soumis
              return true;
          });
      }
  }
});

