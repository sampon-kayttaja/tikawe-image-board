# tikawe-image-board

Suunnitelma:

- Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen.
- Käyttäjä pystyy lisäämään, muokkaamaan ja poistamaan postauksia.
- Käyttäjä pystyy lisäämään kuvia tai videoita postauksiin.
- Käyttäjä näkee sovellukseen lisätyt postaukset.
- Käyttäjä pystyy etsimään postauksia hakusanalla.
- Sovelluksessa on käyttäjäsivut, jotka näyttävät tilastoja ja käyttäjän lisäämät postaukset.
- Käyttäjä pystyy valitsemaan postaukselle aiheen ja hakea muita postauksia aiheen perusteella.
- Käyttäjä pystyy tykkäämään postauksista.
- Käyttäjä pystyy kommentoimaan postauksiin.
- Sovelluksen tarkoitus on olla instagram tyylinen kuvien ja videoitten jakamis palvelu.
- Käyttäjä voi seurata muiden tilejä ja nähdä näiden postaukset etusivulla


Sovelluksessa pystyy tällä hetkellä:

- Luoda käyttäjän
- Kirjautua sisään ja ulos
- Luoda postauksen ja poistaa oman postauksen
- Tykätä postauksista ja poistaa oman tykkäyksen
- Kommentoida ja poistaa oman kommentin
- Etsiä postauksia otsikon perusteella
- Järjestää postaukset tykkäysten ja julkaisu ajan perusteella


# sovelluksen käynnistäminen

Suorita repositorion juuressa:

1. python3 -m venv venv

2. source venv/bin/activate

3. pip install -r requirements.txt

4. mkdir -p instance

5. sqlite3 instance/database.db < app/schema.sql

6. flask run
