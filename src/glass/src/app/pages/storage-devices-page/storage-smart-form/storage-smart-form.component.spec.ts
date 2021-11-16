import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TranslateModule } from '@ngx-translate/core';

import { PagesModule } from '~/app/pages/pages.module';
import { StorageSmartFormComponent } from '~/app/pages/storage-devices-page/storage-smart-form/storage-smart-form.component';
import { TestingModule } from '~/app/testing.module';

describe('StorageSmartPageComponent', () => {
  let component: StorageSmartFormComponent;
  let fixture: ComponentFixture<StorageSmartFormComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PagesModule, TestingModule, TranslateModule.forRoot()]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(StorageSmartFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
