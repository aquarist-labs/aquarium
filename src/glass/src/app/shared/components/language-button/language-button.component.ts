import { Component } from '@angular/core';

import { getCurrentLanguage, setCurrentLanguage, supportedLanguages } from '~/app/i18n.helper';

@Component({
  selector: 'glass-language-button',
  templateUrl: './language-button.component.html',
  styleUrls: ['./language-button.component.scss']
})
export class LanguageButtonComponent {
  languages = supportedLanguages;
  currentLanguage: string;

  constructor() {
    this.currentLanguage = getCurrentLanguage();
  }

  onSelectLanguage(language: string): void {
    setCurrentLanguage(language);
    document.location.replace('');
  }
}
