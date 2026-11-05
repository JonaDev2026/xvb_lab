import hashlib
import os

from core.config import leggi_config, scrivi_config, CARTELLE_LISTE, CARTELLE_VECCHIE
from core.playlists import (
    categorie, categorie_m3u, leggi_lista, liste_in_cartella, nome_di, NOMI_URL, CACHE_LISTE
)
from core.epg import leggi_epg, prendi_epg, unisci_guide, nome_dentro, EPG_ICONE, EPG_ICONE_NOME
from core.favorites import leggi_preferiti_cat, PREF_MUSICA, PREF_VIDEO


class Sessione:
    def __init__(self):
        self.config = leggi_config()
        self.liste = []
        self.canali = []
        self.epg_nomi = {}
        self.epg = {}
        self.preferiti = []
        self.preferiti_musica = []
        self.preferiti_video = []
        self.carica_liste()
        self.carica_preferiti()

    def tutte_le_liste(self):
        fuori = liste_in_cartella()
        gruppi = {}
        for nome, dentro in categorie():
            if nome.lower() != "favorite":
                fuori.extend(dentro)
                for percorso in dentro:
                    gruppi[percorso] = nome
        buone = []
        for percorso in self.config.get("liste", []):
            if (isinstance(percorso, str) and percorso
                    and not percorso.startswith("http")
                    and os.path.isfile(percorso)
                    and percorso not in fuori
                    and os.path.dirname(os.path.abspath(percorso))
                    not in CARTELLE_LISTE + CARTELLE_VECCHIE):
                buone.append(percorso)
        if buone != self.config.get("liste", []):
            self.config["liste"] = buone
            from core.config import scrivi_config
            scrivi_config(self.config)
        NOMI_URL.clear()
        NOMI_URL.update(self.config.get("nomi_liste", {}))
        NOMI_URL.update(self.config.get("liste_url", {}))
        percorsi = fuori + buone + list(self.config.get("liste_url", {}))
        unici = []
        viste = set()
        for percorso in percorsi:
            if percorso not in viste:
                viste.add(percorso)
                unici.append(percorso)
        return unici, gruppi

    def carica_liste(self):
        percorsi, gruppi = self.tutte_le_liste()
        for percorso in percorsi:
            if percorso.startswith(("http://", "https://")):
                cache = os.path.join(CACHE_LISTE, hashlib.md5(percorso.encode()).hexdigest() + ".m3u")
                if not os.path.isfile(cache):
                    continue
            try:
                canali = leggi_lista(percorso)
                categorie_lista = categorie_m3u(percorso)
            except Exception:
                continue
            gruppo = gruppi.get(percorso)
            voce = {
                "percorso": percorso,
                "nome": nome_di(percorso),
                "gruppo": gruppo,
                "canali": canali,
                "categorie": categorie_lista,
            }
            self.liste.append(voce)
            for nome, url, ide in canali:
                self.canali.append((
                    nome, url, ide, categorie_lista.get(url, "Altri"), percorso
                ))

    def carica_preferiti(self):
        try:
            self.preferiti = leggi_preferiti_cat()
        except Exception:
            self.preferiti = []
        for nome, url, ide, categoria in self.preferiti:
            self.canali.append((nome, url, ide, categoria or "MyPlaylist", "__favorite__"))
        try:
            self.preferiti_musica = leggi_preferiti_cat(PREF_MUSICA)
            self.preferiti_video = leggi_preferiti_cat(PREF_VIDEO)
        except Exception:
            self.preferiti_musica, self.preferiti_video = [], []
        for nome, url, ide, categoria in self.preferiti_musica:
            self.canali.append((nome, url, ide, categoria or "Music", "__favorite_music__"))
        for nome, url, ide, categoria in self.preferiti_video:
            self.canali.append((nome, url, ide, categoria or "Video", "__favorite_video__"))

    def carica_guide(self, silenzioso=False):
        EPG_ICONE.clear()
        EPG_ICONE_NOME.clear()
        guide = []
        percorsi = self.config.get("epg", [])
        if isinstance(percorsi, str):
            percorsi = [percorsi] if percorsi else []
        for percorso in percorsi:
            try:
                file_epg = prendi_epg(percorso)
                nome = nome_dentro(file_epg)
                if nome:
                    self.config.setdefault("epg_nomi", {})[percorso] = nome
                    scrivi_config(self.config)
                guide.append(leggi_epg(file_epg))
            except Exception:
                continue
        if guide or not silenzioso:
            self.epg_nomi, self.epg = unisci_guide(guide)

    def categorie(self, percorso=None):
        nomi = set()
        for lista in self.liste:
            if percorso is None or lista["percorso"] == percorso:
                nomi.update(lista["categorie"].values())
        return sorted(nomi, key=str.casefold)

    def canali_per(self, percorso=None, categoria=None, ricerca=""):
        q = (ricerca or "").casefold()
        return [
            voce for voce in self.canali
            if (percorso is None or voce[4] == percorso)
            and (categoria is None or voce[3] == categoria)
            and (not q or q in voce[0].casefold())
        ]
