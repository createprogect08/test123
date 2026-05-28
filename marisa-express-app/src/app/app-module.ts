import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { AppRoutingModule } from './app-routing-module';
import { App } from './app';
import { JwtInterceptor } from './interceptors/jwt.interceptor';
import { HeaderComponent } from './components/header/header';
import { CartPanelComponent } from './components/cart-panel/cart-panel';
import { LandingComponent } from './components/landing/landing';
import { RestaurantListComponent } from './components/restaurant-list/restaurant-list';
import { RestaurantDetailComponent } from './components/restaurant-detail/restaurant-detail';
import { CheckoutComponent } from './components/checkout/checkout';
import { OrderTrackingComponent } from './components/order-tracking/order-tracking';
import { TeamComponent } from './components/team/team';
import { StoricoComponent } from './components/storico/storico';
import { WalletComponent } from './components/wallet/wallet';
import { SettingComponent } from './components/setting/setting';

@NgModule({
  declarations: [
    App,
    HeaderComponent,
    CartPanelComponent,
    LandingComponent,
    RestaurantListComponent,
    RestaurantDetailComponent,
    CheckoutComponent,
    OrderTrackingComponent,
    TeamComponent,
    StoricoComponent,
    WalletComponent,
    SettingComponent
  ],
  imports: [
    BrowserModule,
    CommonModule,
    AppRoutingModule,
    HttpClientModule,
    FormsModule,
    ReactiveFormsModule
  ],
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: JwtInterceptor, multi: true }
  ],
  bootstrap: [App]
})
export class AppModule { }
