import googlemaps
import json
import hashlib
import os
import time
import re
import numpy as np
from datetime import datetime
from haversine import haversine, Unit
from scipy.spatial import cKDTree

class GeocodeCache:
    def __init__(self, cache_file="geocode_cache.json"):
        self.cache_file = cache_file
        self.cache = {}
        self.hits = 0
        self.misses = 0
        self.contexto_geografico = "" 
        self.carregar_cache()
    
    def definir_contexto(self, contexto):
        self.contexto_geografico = contexto.strip().upper()
    
    def _gerar_chave(self, endereco):
        endereco_normalizado = str(endereco).strip().upper()
        chave_completa = f"{endereco_normalizado}|{self.contexto_geografico}"
        return hashlib.md5(chave_completa.encode()).hexdigest()
    
    def carregar_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except: self.cache = {}

    def salvar_cache(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except: pass
    
    def buscar(self, endereco):
        chave = self._gerar_chave(endereco)
        if chave in self.cache:
            self.hits += 1
            return self.cache[chave]
        self.misses += 1
        return None
    
    def adicionar(self, endereco, dados_geo):
        chave = self._gerar_chave(endereco)
        self.cache[chave] = {
            'dados': dados_geo,
            'timestamp': datetime.now().isoformat(),
            'endereco_original': endereco,
            'contexto': self.contexto_geografico
        }
    
    def obter_estatisticas(self):
        total = self.hits + self.misses
        taxa = (self.hits / total * 100) if total > 0 else 0
        return {'total': len(self.cache), 'hits': self.hits, 'misses': self.misses, 'taxa': taxa}

class GeoService:
    def __init__(self, api_key, local_ref, modo_operacao):
        self.client = googlemaps.Client(key=api_key)
        self.local_ref = local_ref
        self.modo_operacao = modo_operacao
        self.cache = GeocodeCache()
        self.cache.definir_contexto(local_ref)
        self.novos_count = 0
        self.tree = None
        self.locais_db = []

    def geocodificar(self, end_bruto):
        busca = str(end_bruto).upper().strip()
        if self.local_ref not in busca: busca += f", {self.local_ref}"
        if "BRASIL" not in busca: busca += ", BRASIL"
        
        # 1. Cache Check
        cached = self.cache.buscar(busca)
        if cached: return cached['dados']

        # 2. API Call
        try:
            res = self.client.geocode(busca)
            if res:
                geo = res[0]['geometry']['location']
                comps = res[0]['address_components']
                info = {'lat': geo['lat'], 'lng': geo['lng'], 'logradouro': '', 'numero': 'S/N', 'bairro': '', 'cep': '', 'cidade': 'NAO IDENTIFICADA'}
                
                for c in comps:
                    t = c['types']
                    if 'route' in t: info['logradouro'] = c['long_name'].upper()
                    if 'street_number' in t: info['numero'] = c['long_name']
                    if 'sublocality' in t: info['bairro'] = c['long_name'].upper()
                    if 'postal_code' in t: info['cep'] = c['long_name']
                    if 'administrative_area_level_2' in t: info['cidade'] = c['long_name'].upper()
                
                if self.modo_operacao == "MUNICIPAL" and info['cidade'] == 'NAO IDENTIFICADA':
                    info['cidade'] = self.local_ref
                
                self.cache.adicionar(busca, info)
                self.novos_count += 1
                
                # Checkpoint de salvamento
                if self.novos_count >= 20:
                    self.cache.salvar_cache()
                    self.novos_count = 0
                
                time.sleep(0.15)
                return info
        except:
            return None
        return None

    def construir_kdtree(self, lista_locais):
        """Cria o índice espacial para busca rápida."""
        self.locais_db = lista_locais
        if len(lista_locais) > 0:
            coords = np.array([list(x['coords']) for x in lista_locais])
            self.tree = cKDTree(coords)
            return True
        return False

    def buscar_vizinho_proximo(self, lat, lng, raio_max_metros):
        """Usa a KD-Tree para achar o vizinho mais próximo instantaneamente."""
        if not self.tree: return None, None, 999999

        coord_c = [lat, lng]
        # Query na árvore (retorna distância em graus e índice)
        dist_graus, indice = self.tree.query(coord_c, k=1)
        
        candidato = self.locais_db[indice]
        
        # Validação precisa (Haversine em metros)
        dist_metros = haversine(coord_c, candidato['coords'], unit=Unit.METERS)
        
        if dist_metros <= raio_max_metros:
            return candidato['Secretaria'], candidato['Localidade'], dist_metros
        
        return "NAO IDENTIFICADO", "LOCAL NAO CADASTRADO", dist_metros

    @staticmethod
    def refinar_endereco_regex(texto_bruto):
        """Separa endereço 'Rua X, 123, Bairro' se o Google falhar."""
        match = re.match(r"^(.*?),\s*(\d+|S/?N)(.*)$", texto_bruto, re.IGNORECASE)
        log, num, bai = texto_bruto, "S/N", ""
        
        if match:
            log = match.group(1).strip().upper()
            num = match.group(2).strip().upper()
            resto = match.group(3).strip()
            if resto:
                bai = resto.replace(",", "").replace("-", "").strip().upper()
                if len(bai) > 3 and bai[-2:] in ["SP", "MG", "RJ", "ES"]: 
                    bai = bai[:-2].strip()
        return log, num, bai