# wpa-quiz
Mały skrypt, który pomaga przygotować się do egzaminu teoretycznego pozwolenia na broń, które są organizowane przez WPA Policji.

Można wygenerować pliki z odpowiedziami. Przy dostarczeniu klucza odpowiedzi, zostanie to sprawdzone.

# Plik z pytaniami
Plik należy wziąć ze strony WPA, zapisać jako zwykły plik txt.

Skrypt testowany na Gdańskim WPA
https://pomorska.bip.policja.gov.pl/KPG/pozwolenia-na-bron/40360,Baza-pytan-egzaminacyjnych.html

# Weryfikacja na podstawie pliku
Quiz można zrzucić do pliku, nawet nie posiadając pliku z kluczem. Można go też wczytać i porównać z kluczem po jego otrzymaniu.
Można w ten sposób przeprowadzić egzamin, a potem go automatycznie zweryfikować wsadowo.

# Wywołanie
```
./wpa-quiz.py

Użycie:
  quiz.py PLIK_PYTAN.txt [-c N] [-r RANGES] [-a user.csv] [-b] [-S]
  quiz.py -a user.csv -v master.csv

Opcje:
  --count=N     | -c N         liczba pytań (domyślnie 20)
  --range=X-Y   | -r X-Y       zakresy pytań, np. 1-50,120-150
  --answers=CSV | -a CSV       klucz odpowiedzi
  --verify=CSV  | -v CSV       porównanie user.csv z master.csv
  --browse      | -b           tryb przeglądania (od razu pokazuje wynik pytania)
  --no-stats    | -S           wyłącza system statystyk
```
# Przykłady użycia

Najprostsze proste wywołanie w podstawowym trybie, z domyślnymi wartościami:
```
$ wpa-quiz.py pytania/PYTANIA_EGZAMINACYJNE.txt
```

Daj 4 pytania i od razu pokazuj czy odpowiedź jest prawidłowa (tryb nieegzaminacyjny):
```
$ wpa-quiz.py pytania/PYTANIA_EGZAMINACYJNE.txt -c 4 -b
```

Wyłącza statystyki (czyli każde pytanie ma takie samo prawdopodobieństwo pojawienia się):
```
$ wpa-quiz.py pytania/PYTANIA_EGZAMINACYJNE.txt -S
```
