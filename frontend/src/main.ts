import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/AppConfig';
import { AppComponent } from './app/AppComponent';

bootstrapApplication(AppComponent, appConfig)
  .catch((err) => console.error(err));
