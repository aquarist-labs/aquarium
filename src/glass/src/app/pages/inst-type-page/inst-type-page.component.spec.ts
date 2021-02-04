import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InstTypePageComponent } from './inst-type-page.component';

describe('InsttypePageComponent', () => {
  let component: InstTypePageComponent;
  let fixture: ComponentFixture<InstTypePageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [InstTypePageComponent]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(InstTypePageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
