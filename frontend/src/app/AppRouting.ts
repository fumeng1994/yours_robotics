import { Routes } from '@angular/router';
import { LandingComponent } from './landing/LandingComponent';
import { RobotDetailComponent } from './robot/RobotDetailComponent';

export const routes: Routes = [
  { path: '', component: LandingComponent },
  { path: ':id', component: RobotDetailComponent }
];