import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { RiderService } from './rider';

export interface Posizione {
  lat: number;
  lng: number;
  accuracy?: number;
}

// Posizione di fallback (Milano centro) quando GPS non disponibile
const FALLBACK: Posizione = { lat: 45.4654, lng: 9.1859 };

@Injectable({ providedIn: 'root' })
export class GeolocationService implements OnDestroy {

  posizione$ = new BehaviorSubject<Posizione | null>(null);

  private watchId:   number | null = null;
  private intervalId: any          = null;
  private invioAttivo               = false;

  constructor(private riderService: RiderService) {}

  getPosizione(): Promise<Posizione> {
    return new Promise((resolve) => {
      if (!navigator.geolocation) { resolve(FALLBACK); return; }
      navigator.geolocation.getCurrentPosition(
        pos => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude, accuracy: pos.coords.accuracy }),
        ()  => resolve(FALLBACK),
        { enableHighAccuracy: true, timeout: 5000 }
      );
    });
  }

  startTracking(): void {
    // Emetti subito il fallback così la mappa ha subito una posizione
    this.posizione$.next(FALLBACK);

    if (!navigator.geolocation) return;

    this.watchId = navigator.geolocation.watchPosition(
      pos => {
        this.posizione$.next({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          accuracy: pos.coords.accuracy
        });
      },
      err => console.warn('GPS non disponibile, uso posizione di test:', err.message),
      { enableHighAccuracy: true, maximumAge: 5000 }
    );
  }

  stopTracking(): void {
    if (this.watchId !== null) {
      navigator.geolocation.clearWatch(this.watchId);
      this.watchId = null;
    }
  }

  startInvioPostura(idOrdine: number): void {
    if (this.invioAttivo) return;
    this.invioAttivo = true;

    const invia = () => {
      const pos = this.posizione$.value || FALLBACK;
      this.riderService.aggiornaPostura(pos.lat, pos.lng).subscribe({
        error: e => console.warn('Errore invio posizione:', e)
      });
    };

    invia();
    this.intervalId = setInterval(invia, 10000);
  }

  stopInvioPostura(): void {
    if (this.intervalId) { clearInterval(this.intervalId); this.intervalId = null; }
    this.invioAttivo = false;
  }

  ngOnDestroy(): void {
    this.stopTracking();
    this.stopInvioPostura();
  }
}
