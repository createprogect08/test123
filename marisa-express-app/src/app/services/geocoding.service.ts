import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { map, debounceTime, distinctUntilChanged, switchMap, catchError } from 'rxjs/operators';
import { Subject } from 'rxjs';

export interface GeoResult {
  lat: number;
  lng: number;
  displayName: string;
  shortName: string;
}

@Injectable({ providedIn: 'root' })
export class GeocodingService {
  private readonly NOMINATIM = 'https://nominatim.openstreetmap.org';

  constructor(private http: HttpClient) {}

  geocode(address: string): Observable<GeoResult> {
    const url = `${this.NOMINATIM}/search?q=${encodeURIComponent(address)}&format=json&limit=1&countrycodes=it&addressdetails=1`;
    return this.http.get<any[]>(url, {
      headers: { 'Accept-Language': 'it' }
    }).pipe(
      map(results => {
        if (!results || results.length === 0) throw new Error('Indirizzo non trovato');
        const r = results[0];
        return {
          lat: parseFloat(r.lat),
          lng: parseFloat(r.lon),
          displayName: r.display_name,
          shortName: this.buildShortName(r)
        };
      })
    );
  }

  suggest(query: string): Observable<GeoResult[]> {
    if (!query || query.length < 3) return of([]);
    const url = `${this.NOMINATIM}/search?q=${encodeURIComponent(query)}&format=json&limit=5&countrycodes=it&addressdetails=1`;
    return this.http.get<any[]>(url, {
      headers: { 'Accept-Language': 'it' }
    }).pipe(
      map(results => (results || []).map(r => ({
        lat: parseFloat(r.lat),
        lng: parseFloat(r.lon),
        displayName: r.display_name,
        shortName: this.buildShortName(r)
      }))),
      catchError(() => of([]))
    );
  }

  reverseGeocode(lat: number, lng: number): Observable<string> {
    const url = `${this.NOMINATIM}/reverse?lat=${lat}&lon=${lng}&format=json&addressdetails=1`;
    return this.http.get<any>(url, {
      headers: { 'Accept-Language': 'it' }
    }).pipe(
      map(r => this.buildShortName(r))
    );
  }

  private buildShortName(r: any): string {
    const a = r.address || {};
    const parts = [];
    if (a.road) parts.push(a.road + (a.house_number ? ' ' + a.house_number : ''));
    if (a.city || a.town || a.village || a.municipality)
      parts.push(a.city || a.town || a.village || a.municipality);
    if (a.state) parts.push(a.state);
    return parts.length > 0 ? parts.join(', ') : r.display_name;
  }
}
