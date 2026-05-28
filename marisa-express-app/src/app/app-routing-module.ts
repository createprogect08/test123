import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { LandingComponent } from './components/landing/landing';
import { RestaurantListComponent } from './components/restaurant-list/restaurant-list';
import { RestaurantDetailComponent } from './components/restaurant-detail/restaurant-detail';
import { CheckoutComponent } from './components/checkout/checkout';
import { OrderTrackingComponent } from './components/order-tracking/order-tracking';
import { TeamComponent } from './components/team/team';
import { StoricoComponent } from './components/storico/storico';
import { WalletComponent } from './components/wallet/wallet';
import { SettingComponent } from './components/setting/setting';

const routes: Routes = [
  { path: '',               component: LandingComponent },
  { path: 'restaurant',     component: RestaurantListComponent },
  { path: 'restaurant/:id', component: RestaurantDetailComponent },
  { path: 'checkout',       component: CheckoutComponent },
  { path: 'order/:id',      component: OrderTrackingComponent },
  { path: 'team',           component: TeamComponent },
  { path: 'storico',        component: StoricoComponent },
  { path: 'wallet',         component: WalletComponent },
  { path: 'setting',        component: SettingComponent },
  { path: '**',             redirectTo: '' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
