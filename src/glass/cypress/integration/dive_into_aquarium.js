describe('Dive into Aquarium', () => {
  it('Visit the first tank', () => {
    cy.intercept('GET', '/api/local/status', { fixture: 'node_qualified.json' });

    cy.visit('/');
    cy.contains('Welcome to Aquarium').should('be.visible');
    cy.clickButton('Check requirements now');
    cy.contains('Congratulations! You can now proceed.');
    cy.clickButton('Next');
    cy.contains('Create new cluster').should('be.visible');
    cy.clickButton('Create');
    cy.contains('This wizard will guide you through the installation process').should('be.visible');
    cy.contains('Start');
    cy.contains('Networking');
    cy.contains('Time');
    cy.contains('Devices');
    cy.contains('Installation');
    cy.contains('Finish');
    cy.contains('Next');
    cy.clickButton('Next');
    cy.contains('Hostname').should('be.visible');
    cy.contains('div', 'Hostname').find('input').type('foohost{enter}');
    cy.clickButton('Next');
    cy.contains('Use an NTP host on the Internet').should('be.visible').click();
    cy.clickButton('Next');
    cy.contains('The following devices have been identified in the system').should('be.visible');
    cy.clickButton('Next');
    cy.contains('Aquarium will now install and setup the core system.').should('be.visible');
    cy.clickButton('Install');
  });
});
